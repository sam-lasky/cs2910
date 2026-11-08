import threading
import sys
import subprocess
from collections.abc import Callable


def create_thread(target_fn:Callable,ssh_process:subprocess.Popen,timeout:int):
    response=[]
    thread =threading.Thread(
        target=target_fn,
        args=(ssh_process,response),
        daemon=True
    )
    thread.start()
    thread.join(timeout=timeout)

    # Thread is dead && response is not empty: return response
    if not thread.is_alive() and response:
        return response[0]
    # Return None (thread still running (timeout) OR empty response list)
    else: return None
