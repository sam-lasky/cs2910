import threading
import sys
import subprocess
from collections.abc import Callable


def create_thread(target_fn, ssh_process):
    response = []
    thread = threading.Thread(
        target=target_fn,
        args=(ssh_process, response),
        daemon=True
    )
    thread.start()
    return thread, response

# active threads = list where each element is a tuple in the form:
#  (machine_id, thread, thread_response)
def wait_for_threads(active_threads, timeout=3):
    results = {}
    for machine_id, thread, response in active_threads:
        thread.join(timeout=timeout)
        results[machine_id]=response[0] if not thread.is_alive() and response else None
    return results

def add_thread(active_threads, machine_id, target_fn, ssh_process):
    thread, response = create_thread(target_fn, ssh_process)
    active_threads.append((machine_id, thread, response))

def send_and_create_thread(active_threads, machine_id, ssh_process,
                           command, write_fn, read_fn):
    write_fn(ssh_process, command)
    add_thread(active_threads, machine_id, read_fn, ssh_process)