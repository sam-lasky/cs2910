import sys, subprocess, time, os

def main():

    # update the git repo, cwd=cs2910
    p = subprocess.run(
        ["git","pull"],
        text=True
    )





if __name__=="__main__":
    main()