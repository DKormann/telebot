__results_str = ""
def _print(*args,end = "\n"):
    global __results_str
    for arg in args:
        __results_str += str(arg)
    __results_str += end

namespace = {"print":_print }


def execute_code (code:str):
    global __results_str
    __results_str = ""
    global namespace
    exec(code,namespace)
    loc = locals()
    for k in loc.keys():
        namespace[k] = loc[k]
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

def set_timer(seconds: int, description: str, context):
    context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)
