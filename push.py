import sys, subprocess, time, os
from datetime import datetime

def check_out(p:subprocess.CompletedProcess):
    # success
    if p.returncode==0:
        print(p.stdout)
    # failure
    else:
        print("STDOUT:", p.stdout)
        print("STDERR:", p.stderr)
        print("Return code:", p.returncode)
        print("Updates were not pushed")
        exit(1)


def main():
    for command in ['git add .',f'git commit -m "{datetime.now()}"' , "git push origin main"]:
        p=subprocess.run(command, shell=True,capture_output=True,text=True)    
        check_out(p)
    print("Updates successfully pushed\n\n")

if __name__=="__main__":
    main()