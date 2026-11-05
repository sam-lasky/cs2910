import os
import os
import platform
import subprocess
from datetime import datetime
import time

a,b,c,=4,9,23
while(True):
    subprocess.run('cls' if platform.system()=='Windows' else 'clear', shell=True)
    print(f"The {a+b} right now is {datetime.now()}")
    print(f"The {b+c} right now is {datetime.now()}")
    print(f"The {c+a} right now is {datetime.now()}")
    a+=3
    b+=5
    c+=7
    time.sleep(1)

subprocess.run('cls' if platform.system()=='Windows' else 'clear', shell=True)
