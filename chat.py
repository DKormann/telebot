from openai import OpenAI
import os
from typing import Literal
from methods import execute_code, evaluate_code
import json


client = OpenAI(
  api_key=os.environ.get("RIVERKEY"),
)

sysprompt = "You are Akira a helpfull chat assistant."

Role = Literal["user","assistant","system"]

tools = [
  {
    "type": "function",
    "function": {
      "name": "exec",
      "description": "Execute any python code, if you cannot answer a request straight up. The exec function does not return values. You need to print results.",
      "parameters": {
        "type": "object",
        "properties": {
          "code": {
            "type": "string",
            "description": "python code to execute",
          },
        },
        "required": ["code"],
      },
    },
  },
  # {
  #   "type": "function",
  #   "function": {
  #     "name": "create_function",
  #     "description": "create a new python function.",
  #     "parameters": {
  #       "type": "object",
  #       "properties": {
  #         "title": {
  #           "type": "string",
  #           "description": "only the title of the new function",
  #         },
  #         "description":{
  #           "type": "string",
  #           "description": "description of the function that should be created.",
  #         }
  #       },
  #       "required": ["title","description"],
  #     },
  #   },
  # },
  {
    "type": "function",
    "function": {
      "name": "timer",
      "description": "Set a timer for x seconds in the future.",
      "parameters": {
        "type": "object",
        "properties": {
          "seconds": {
            "type": "number",
            "description": "delay in seconds",
          },
          "description":{
            "type": "string",
            "description": "short description or message for the timer"
          }
        },
        "required": ["seconds","description"],
      },
    },
  },
  {
    "type": "function",
    "function": {
      "name": "remove_timer",
      "description": "remove the timer with given description, returns True if the timer was found and removed.",
      "parameters": {
        "type": "object",
        "properties": {
          "description": {
            "type": "string",
            "description": "description of the timer",
          },
        },
        "required": ["description"],
      },
    },
  },
]


class ChatSession:

  def __init__(self, ctx, chat_id):
    self.id = chat_id
    self.ctx = ctx
    self.history = [
      {"role": "system", "content": sysprompt},
      ]
    self.reply_buffer = ""

    self.methods = {
      "exec": execute_code,
      "python": execute_code,
      "create_function": self.create_function,
      "timer": self.timer,
      "remove_timer": self.remove_timer,
    }

  def create_function(self, title:str, description:str):
    print('creating function', title)
    messages = self.history[-5:-1]

    messages += [{"role":"system","content":f"write the function {title}. {description}"}]

    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages = messages,
      stream = False
    )

    code = completion.choices[0].message.content

    print()
    print()
    print(code)
    print()
    print()


  async def alarm(self,context):
    job = context.job
    # await self.send(f"{job.name}")
    self.add_message("system", f"timer finished: {job.name}")
    await self.react()

  def timer(self,seconds:int,description:str):
    self.ctx.job_queue.run_once(self.alarm, seconds, chat_id=self.id, name=description, data=seconds)

  def remove_timer(self,description):
    current_jobs = self.ctx.job_queue.get_jobs_by_name(description)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

  def add_message(self, role:Role,content:str): self.history.append({"role":role,"content":content})

  def reset (self):
    self.history = [{"role": "system", "content": sysprompt},]

  async def react(self,messages = None):
    print("interacting ...")
    if messages is None: messages = self.history
    print(messages)
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages = self.history[-10:],
      tools = tools,
      stream =True
    )
    assistant_message = ""

    for chunk in completion:
      if chunk.choices[0].delta.tool_calls:
        await self.func_call(chunk.choices[0].delta.tool_calls[0], completion)
      content = chunk.choices[0].delta.content
      if not content is None:
        assistant_message += content
        await self.send_message(content, end="",flush=True)
    await self.send_message()

    self.add_message("assistant",assistant_message)

  async def func_call(self,toolcall, completion):
    print('calling function',toolcall.function.name)
    args = ""
    for chunk in completion:
      call = chunk.choices[0].delta.tool_calls
      if call:
        args += call[0].function.arguments
      else:
        try: args = json.loads(args)
        except:pass
        print(args)
        if type(args) == dict:
          ret = self.methods[toolcall.function.name](**args)
        else:
          ret = self.methods[toolcall.function.name](args)
        ret = str(ret)[-200:]

        fn_msg = f"Executed function call {toolcall.function.name}({args}). Response: {ret if not (ret is None) else 'ok'}."
        print(fn_msg)

        self.add_message("system", fn_msg)
        await self.react()

  async def answer_chat_message(self, msg:str):
    self.add_message("user",msg)
    await self.react()

  async def send(self,msg):
    await self.ctx.bot.send_message(chat_id = self.id,text=msg)

  async def send_message(self,msg = "" ,end="\n",flush = False):
      self.reply_buffer += msg + end
      if self.reply_buffer.count("```")  == 1: return # wait for end of code
      if self.reply_buffer.count("```") == 2:
          await self.send(self.reply_buffer)
          self.reply_buffer = ""
      buf = self.reply_buffer.split("\n")
      for p in buf[:-1]:
          if p != "" : await self.send(p)
      self.reply_buffer = buf[-1]


