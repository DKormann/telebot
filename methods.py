__results_str = ""
def _print(*args,end = "\n"):
    global __results_str
    for arg in args:
        __results_str += "\n" + str(arg)
    __results_str += end

namespace = {"print":_print }


def execute_code (code:str):
    print("executin")
    global __results_str
    __results_str = ""
    global namespace
    exec(code,namespace)
    loc = locals()
    for k in loc.keys():
        namespace[k] = loc[k]

    last_line = code.split("\n")[-1]
    if last_line.lstrip() == last_line:
        try: __results_str += "\n" + str(eval(last_line,namespace))
        except Exception as e: print('error on lastline',e)
    return __results_str

def evaluate_code (code:str):
    global __results_str
    __results_str = ""
    global namespace
    ret = eval(code,namespace)
    loc = locals()
    for k in loc.keys():
        namespace[k] = loc[k]
    return __results_str + str(ret)


async def alarm(session,ctx):
    job = ctx.job
    session.add_message("system", f"timer finished: {job.name}")
    await session.react()

def set_timer(seconds: int, description: str,session):
    print("timer set for", seconds)
    session.ctx.job_queue.run_once(lambda ctx :alarm(session,ctx), seconds, chat_id=session.id, name=description, data=seconds)

import datetime

def set_alarm_24h_format(hours: int, minutes: int, description:str, session ):
    delta_hours = hours - datetime.datetime.now().hour
    delta_minutes = minutes - datetime.datetime.now().minute
    due = (delta_hours * 60 + delta_minutes) * 60
    if due < 0 : due += 24 * 60 * 60
    set_timer(due,description,session)