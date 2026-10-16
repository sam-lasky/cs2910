import sys, subprocess, time, os, platform, json

# Update the CS2910 repo & return the directories involved in the update
# if changes were made otherwise return none. 
def update_repo(runtime_config):
    # Check a reboot occurred. If so store the
    # info and skip another pull
    with open('reboot.txt', 'r+') as f:
        # get reboot file 
        file_contents = f.read().strip()
        # Check if a reboot has occurred, indicated by the reboot.txt file 
        # containing text other than 'none'. If one has, get the file conents
        # and fill in the update info, reset the reboot.txt file to none and
        # leave the update_repo func 
        if file_contents!='none':
            runtime_config['update']= file_contents.split(',')
            f.seek(0)
            f.write('none')
            f.truncate()
            print("System reboot completed successfully. Using most up to date repository!\n")
            return

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
    updated_dirs = set()
    # report update status 
    update_status = changes.stdout.splitlines()
    # no change detected 
    if len(update_status)==0:print("No repository updates detected.\n")
    # change detected, record updated directories & report update
    else:
        updated_dirs={d for update in update_status for d in ['docker/','prime/','spines/'] if d in update}
        print("Update detected & applied, rebooting in 5 seconds.....\n")
        with open("reboot.txt", "w") as f:
            f.write(",".join(updated_dirs))
        time.sleep(5)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # add update info to runtime_config (convert to list for eventual JSON serialization)
    runtime_config['update']= list(updated_dirs)
    
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

    # return startup_config
    return startup_config

# Start Docker
def docker_start(runtime_config):
    # tracks all the directories who's files have been modified in order
    # to update images accordingly. 
    modified_directories = runtime_config['update']
    # build the images on auto mode
    # update the configuration files in prime and spines
    p = subprocess.run(
        f"py -3 build.py auto {len(modified_directories)}",
        shell=True,
        cwd='docker/',
        capture_output=True,
        text=True
    )
    print("STDOUT:", repr(p.stdout))
    print("STDERR:", repr(p.stderr))
    print("RETURN CODE:", p.returncode)

# Start aster
def aster_start(runtime_config):
    pass


# [Personalized Startup Config]: python3 run.py <docker|aster> <encrypted|plain> <MAX_PO_IN_FLIGHT >= 1>
# [Default Startup Config]: python3 run.py 
# (default values: environment = docker, unencrypted, MAX_PO_IN_FLIGHT=20)
def main():
    # clear terminal for easier readabilityd
    clear_cmd = 'cls' if platform.system()=='Windows' else 'clear'
    subprocess.run(clear_cmd, shell=True)

    # get the environment, which gets passed as a CLI arg, returns the runtime_config as a dict that holds
    # environment, encryption type, MAX_PO_IN_FLIGHT
    runtime_config=parse_cli(sys.argv)

    # update the repo & get the directories associated with the update (or none if up to date) and store in runtime_config
    update_repo(runtime_config)

    # update the configuration files in prime and spines
    p = subprocess.run(
        f"python config.py {runtime_config['environment']} {runtime_config['encryption']} {runtime_config['max_po']} ",
        shell=True,
        cwd='configure/',
        capture_output=True,
        text=True
    )


    # get the names of the dirs w/ modified files from config.py (if any)
    print("Updating the configuration files for prime & spines...")
    updated_dirs = p.stdout.strip().splitlines()[-1].split(',') if p.stdout.strip() else []
    if p.returncode==0:
        print("Configuration files successfully updated!\n")

    # update the list of updated directories in runtime_config
    runtime_config['update']= list(set(updated_dirs+runtime_config['update']))
    # Hand off control to the startup scripts 
    if runtime_config['environment']=='docker': docker_start(runtime_config)
    else: aster_start(runtime_config)

if __name__=="__main__":
    main()