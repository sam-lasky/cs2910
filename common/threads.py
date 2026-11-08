import threading
import sys
import subprocess
# local 
sys.path.insert(0, "..")
from aster.aster_common import read_from_aster

def create_thread(target_fn:str,ssh_process:subprocess.Popen,timeout:int,msg:str):
    response=[]
    thread =threading.Thread(
        target=target_fn,
        args=(ssh_process,response),
        daemon=True
    )
    thread.start()
    thread.join(timeout=timeout)

    # Thread is dead && response is not empty && the first entry 
    if not thread.is_alive() and response and response[0].strip()=='READY':
        return True
    else: return False


# def read_ssh_output(ssh_process:subprocess.Popen, response:list):
#     response.append(ssh_process.stdout.readline())