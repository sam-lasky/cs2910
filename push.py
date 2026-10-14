import sys, subprocess, time, os
from datetime import datetime

def check_out(p:subprocess.CompletedProcess):
    # success
    if p.returncode==0:
        print(p.stdout)
    # failure
    else:
        print(p.stderr)
        # terminate
        print("Updates were not pushed\n\n")
        exit(1)


def main():
    print("\n\n")
    for command in ["git add .",f"git commit -m {datetime.now()}", "git push origin main"]:
        p=subprocess.run(command, shell=True,capture_output=True)    
        check_out(p)






if __name__=="__main__":
    main()