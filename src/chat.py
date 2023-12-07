import os
from openai import OpenAI
from typing import Literal
from tools import Tools, tools
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

bot_name = os.getenv('BOT_NAME')

sysprompt = f"You are {bot_name} a helpful chat assistant."

Role = Literal["user", "assistant", "system"]



class ChatSession:
    def __init__(self, ctx, chat_id):
        self.id = chat_id
        self.ctx = ctx
        self.debug_mode = False
        self.is_admin = False
        self.history = [
            {"role": "system", "content": sysprompt},
        ]

        self.tools = Tools(self)
    
    def toggle_debug_mode(self):self.debug_mode = not self.debug_mode

    async def log(self,*args, **kwargs):
        print(*args)
        if self.debug_mode: await self.send_message("<log>: "+str(args))

    def add_message(self, role: Role, content: str): self.history.append(
        {"role": role, "content": content})

    def reset(self): self.history = [{"role": "system", "content": sysprompt},]

    async def react(self):
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.history[-10:],
            tools=tools
        )

        if completion.choices[0].message.content:
            await self.send_message(completion.choices[0].message.content)

        if completion.choices[0].message.tool_calls:
            await self.tools.tool_call(completion.choices[0].message.tool_calls[0])

    async def answer_chat_message(self, msg: str):
        self.add_message("user", msg)
        await self.react()

    async def send_document(self, doc):
        await self.ctx.bot.send_document(chat_id=self.id, document=doc)

    async def send_message(self, msg: str):
        self.add_message("assistant", msg)
        await self.ctx.bot.send_message(chat_id=self.id, text=msg)
