import sys, subprocess, time, os, platform, json

# Update the CS2910 repo & return the directories involved in the update
# if changes were made otherwise return none. 
def update_repo():
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

    # used to store directories that were updated
    updated_dirs = None
    # report update status 
    update_status = changes.stdout.splitlines()
    # no change detected 
    if len(update_status)==0:print("No repository updates detected.")
    # change detected, record updated directories & report update
    else:
        updated_dirs={d for update in update_status for d in ['docker/','prime/','spines/'] if d in update}
        print("Repository has been successfully updated.")
    # return the dirs in the update
    return updated_dirs

# Usage
def usage():
    print("Usage:")
    print("  Custom:  python3 run.py <docker|aster> <encrypted|plain> <MAX_PO_IN_FLIGHT >= 1>")
    print("  Default: python3 run.py")
    print("           (docker, plain, MAX_PO_IN_FLIGHT=20)")

# Parse CLI passed to the program
def parse_cli(args):
    # startup configuration, default: docker, unencrypted, MAX_PO_IN_FLIGHT = 20
    startup_config = {'environment':'docker', 'encryption':0, 'max_po':20} 
    
    # too many args (either 0 or 3)
    if len(args) not in [1,4]:
        print(f"Error: Expected <0|3> arguments, received {len(sys.argv) - 1}.")
        sys.exit(1)      
    # correct num received 
    if len(args)==4:
        # check if env is correct AND encryption choice is correct AND MAX_PO_IN_FLIGHT val correct
        if (args[1] not in ["docker", "aster"]) or (args[2] not in ["encrypted","plain"]) or (args[3]<1):
            print("Error: Invalid input")
            usage()
            exit(1)
        # CLI args correct, add to dict
        else:
            # update environment
            startup_config['environment']=args[1]
            # update encryption type 
            startup_config['encryption']=args[2]
            # update MAX_PO
            startup_config['max_po']=args[3]

    # Display startup configuration
    print("\n" + "═" * 46)
    print("           STARTUP CONFIGURATION")
    print("═" * 46)
    print(f"  {'Environment':<22} {startup_config['environment']}")
    print(f"  {'Encryption':<22} {'Enabled' if startup_config['encryption'] else 'Disabled'}")
    print(f"  {'MAX_PO_IN_FLIGHT':<22} {startup_config['max_po']}")
    print("═" * 46 + "\n")

    # Write to startup_config.json so subsequent scripts can refer to this information
    with open('startup_config.json', 'w') as f:
        json.dump(startup_config, f, indent=4)

# [Personalized Startup Config]
#       Usage: python3 run.py <docker|aster> <encrypted|plain> <MAX_PO_IN_FLIGHT >= 1>
# [Default Startup Config] (environment = docker, unencrypted, MAX_PO_IN_FLIGHT=20)
#       Usage: python3 run.py 
def main():
    # clear terminal for easier readabilityd
    clear_cmd = 'cls' if platform.system()=='Windows' else 'clear'
    subprocess.run(clear_cmd, shell=True)

    # get the environment, which gets passed as a CLI arg
    parse_cli(sys.argv)

    # update the repo & get the directories associated with the update (or none if up to date)
    updated_dirs = update_repo()
 


if __name__=="__main__":
    main()