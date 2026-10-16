import sys, subprocess, time, os, platform

def main():

    # clear terminal for easier readability
    clear_cmd = 'cls' if platform.system()=='Windows' else 'clear'
    subprocess.run(clear_cmd, shell=True)

    # update the git repo, cwd should already be CS2910
    print("Checking for updates in CS2910 repository...")
    p = subprocess.run(
        ["git","pull"],
        text=True,
        capture_output=True
    )

    # check if repo update attempt successful, otherwise report failure and terminate
    if p.returncode!=0:
        print("Error: Issue updating repo in CS2910/run.py")
        print(f"Error Msg: {p.stderr}")
        print("Terminating program")
        exit(1)

    # get the changes (if any) made to the repo
    changes = subprocess.run(
    ["git", "diff", "--name-only", "ORIG_HEAD", "HEAD"],
    capture_output=True,
    text=True
    )

    # report update status 
    update_status = changes.stdout.splitlines()
    # no change detected 
    if len(update_status)==0:print("No repository updates detected.")
    # change detected, record updated directories & report update
    else:
        pass

if __name__=="__main__":
    main()