import io
import contextlib
import json

from openai import OpenAI
import os
import json
from dotenv import load_dotenv

from inspect import iscoroutine

load_dotenv()

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

tool_file = "src/tools.json"

json_format_function_prompt = """Your response should be in JSON format, like this:
{
    "name": "my_function",
    "description": "my function description",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "param1 description"
            },
        },
        "required": ["param1"]
    },
    code: "async def my_function(param1):\\n    return param1"
}
"""

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
                    "description": {
                        "type": "string",
                        "description": "short description or message for the timer"
                    }
                },
                "required": ["seconds", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_alarm",
            "description": "Set an alarm for a time in the future.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hours": {
                        "type": "number",
                        "description": "hours of the time",
                    },
                    "minutes": {
                        "type": "number",
                        "description": "minutes of the time",
                    },
                    "description": {
                        "type": "string",
                        "description": "short description or message for the timer"
                    }
                },
                "required": ["hours", "minutes", "description"],
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
    {
        "type": "function",
        "function": {
            "name": "create_image",
            "description": "Create an image from a given text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "text to convert to image",
                    },
                    "model": {
                        "type": "string",
                        "description": "model to use for image generation, defaults to dall-e-2",
                        "enum": ["dall-e-2", "dall-e-3"]
                    }
                },
                "required": ["text"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_function",
            "description": "Writes and adds a function to the available tools using a given description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "title of the function",
                    },
                    "description": {
                        "type": "string",
                        "description": "specific description of the function, including the parameters and return value and what exactly the function does.",
                    },
                },
                "required": ["title", "description"],
            },
        },
    }
]



def timer(seconds: int, description: str):
    global chat_session

    class Alarm():
        def __init__(self,chat_session): self.chat_session = chat_session
        async def __call__(self,context):
            job = context.job
            self.chat_session.add_message("system", f"timer finished: {job.name}")
            await self.chat_session.react()

    chat_session.ctx.job_queue.run_once(
        Alarm(chat_session), seconds, chat_id=chat_session.id, name=description, data=seconds)

def set_alarm(hours: int, minutes:int, description: str):
    import datetime
    now_hours = datetime.datetime.now().hour
    now_minutes = datetime.datetime.now().minute

    deltas = (((hours - now_hours) * 60) + minutes - now_minutes)*60
    if deltas < 0 : deltas += 24 * 360
    timer (deltas, description)


class Tools:
    def __init__(self, session):
        self.chat_session = session
        self.methods = {
            "exec": execute_code,
            "python": execute_code,
            "add_function": self.add_function,
            "timer": timer,
            "set_alarm":set_alarm,
            "remove_timer": self.remove_timer,
            "create_image": self.create_image,
        }

        self.load_tools()
        self.print = self.chat_session.log

    def load_tools(self):
        try:
            with open(tool_file) as f:
                # add to tools
                saved_tools = json.load(f)

                # add to methods
                for tool in saved_tools:
                    if tool["type"] == "function":
                        exec(tool["function"]["code"])
                        self.methods[tool["function"]["name"]] = eval(
                            tool["function"]["name"])
                        # remove code from tool
                        del tool["function"]["code"]

                tools.extend(saved_tools)
        except Exception:
            pass

    async def create_image(self, text: str, model="dall-e-3"):
        response = client.images.generate(
            model=model,
            prompt=text,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url

        await self.chat_session.send_document(image_url)

        return "image sent to user"

    async def add_function(self, title: str, description: str):
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role": "system",
                      "content": f"write the function with the title: {title}. this is the {description}. Your function should always be async even if it doesnt need to be. " + json_format_function_prompt}],
            stream=False,
            response_format={"type": "json_object"},
        )

        code = completion.choices[0].message.content

        # convert to json
        code = json.loads(code)

        # append to tools.json
        try:
            with open(tool_file) as f:
                saved_tools = json.load(f)
        except Exception:
            saved_tools = []

        saved_tools.append({
            "type": "function",
            "function": code
        })
        # save to file
        with open(tool_file, "w") as f:
            json.dump(saved_tools, f, indent=4)

        # add function to methods
        exec(code["code"])
        self.methods[code["name"]] = eval(code["name"])
        # add function to tools
        tools.append({
            "type": "function",
            "function": code
        })

        return 'function added'

    async def remove_timer(self, description):
        current_jobs = self.chat_session.ctx.job_queue.get_jobs_by_name(
            description)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    async def tool_call(self, toolcall):
        await self.print('calling function', toolcall.function.name,
              toolcall.function.arguments)

        args = toolcall.function.arguments
        globals()['chat_session'] = self.chat_session
        try:
            args = json.loads(args)
            ret = self.methods[toolcall.function.name](**args)
        except Exception:
            ret = self.methods[toolcall.function.name](args)
        if iscoroutine(ret): ret = await ret

        del globals()['chat_session']

        ret = str(ret)[-500:]

        fn_msg = f"Executed function call {toolcall.function.name}({args}). Response: {ret if (ret is not None) else 'ok'}."
        await self.print(fn_msg)

        self.chat_session.add_message("system", fn_msg)
        await self.chat_session.react()


async def execute_code(code: str):
    # we should do something like this to prevent malicious code execution
    # import builtins
    # safe_builtins = {name: getattr(builtins, name) for name in ['range', 'len', 'int', 'float', 'str']}
    # safe_namespace = {'__builtins__': safe_builtins}
    # exec(code, safe_namespace)

    # Buffer to capture print statements
    output_buffer = io.StringIO()

    # Redirect standard output to the buffer
    with contextlib.redirect_stdout(output_buffer):
        try:
            exec(code)
        except Exception as e:
            return f"Error during execution: {e}\n"

    # Handle the last line for possible output
    last_line = code.split("\n")[-1]
    if last_line.lstrip() == last_line:
        try:
            result = eval(last_line)
            if result is not None:
                output_buffer.write(str(result) + '\n')
        except Exception as e:
            output_buffer.write(f"Error on last line: {e}\n")

    return output_buffer.getvalue()
