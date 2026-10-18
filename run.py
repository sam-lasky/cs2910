import sys, subprocess, time, os, platform, json
from datetime import datetime

# Update the CS2910 repo & record the 
# directories impacted in the env var
# UPDATES for subsequent makes/image builds.
# If an update has occurred, reboot the script 
# in order to use the most current version.  
def update_repo():

    # Check to see if a reboot has occurred, indicated 
    # by the environment variable REBOOT == 1. If it has,
    # report the reboot, reset the variable and return. 
    if os.environ['REBOOT']:
            os.environ['REBOOT']=0
            print("System reboot completed successfully. Using most up to date repository!\n")
            return

    # Update the git repo, cwd should already be CS2910
    print("Checking for updates in CS2910 repository...")
    p = subprocess.run(
        ["git","pull"],
        text=True,
        capture_output=True
    )

    # Check if repo update attempt successful, otherwise report failure and terminate the script. 
    if p.returncode!=0:
        print("Error: Issue updating repo in fn call update_repo in CS2910/run.py")
        print(f"Error Msg: {p.stderr}")
        print("Terminating program...\n")
        exit(1)

    # Get the changes (if any) made to the repo
    changes = subprocess.run(
    ["git", "diff", "--name-only", "ORIG_HEAD", "HEAD"],
    capture_output=True,
    text=True
    )
    # Split the list of changed files into distinct entries
    update_status = changes.stdout.splitlines()
    # No change detected 
    if len(update_status)==0:print("No repository updates detected.\n")
    # Change detected, record affected directories & report update. Store the 
    # directories in the environment variable UPDATES and then reboot the 
    # script. 
    else:
        # Modify the UPDATED environment variable accordingly 
        os.environ['UPDATED']+=' '.join(d for update in update_status for d in ['docker/','prime/','spines/'] if (d in update and d not in os.environ['UPDATED']))

        # Reboot
        os.environ['REBOOT']=='1'
        for i in range(5, 0, -1):
            print(f"\rUpdate detected & applied, rebooting in {i} seconds...", end="", flush=True)
            time.sleep(1)
        print("\rRebooting now!                                      ")
                
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
# Prints Usage
def usage():
    print("Usage:")
    print("python3 run.py <docker|aster> <encrypted|plain> <MAX_PO_IN_FLIGHT (must be >= 1) <NUM_REPLICAS> (must be >=6)")

# Parse CLI passed to the program, check if correct
# values used, store those values as environment variables, initialize
# 'UPDATED' environment variable, print startup config
def parse_cli(args):
    # Invalid # of args
    if len(args) <4 or len(args)>4:
        print('Error: Invalid # of args')
        usage()
        sys.exit(1)      
    # Correct number of args received 
    else:
        # Check if env/encryption/MAX_PO/NUM_REPLICAS choices are correct
        if (args[1] not in ["docker", "aster"]) or (args[2] not in ['encrypted','plain']) or (int(args[3])<1) or (int(args[4])<6):
            print("Error: Invalid input")
            usage()
            exit(1)
        # CLI args correct, create & set the environment variables for each. 
        # Additionally create the UPDATED environment var. 
        else:
            # Create & set environment var for environment <'aster'|'docker'>
            os.environ['ENVIRONMENT']=args[1]
            # Create & set environment var for encryption <'plain'|'encrypted'>
            # Store as 'plain'= '0' & 'encrypted'='1' for convience 
            os.environ['ENCRYPTION']='0' if args[2]=='plain' else '1'
            # Create & set environment var for MAX_PO
            os.environ['MAX_PO']= args[3]
            # Create & set environment var for NUM_REPLICAS
            os.environ['NUM_REPLICAS']= args[3]
            # Create & initialize environment variable for UPDATED to ''
            os.environ['UPDATED']=''

    # Display startup configuration
    print("\n" + "═" * 46)
    print("           STARTUP CONFIGURATION")
    print("═" * 46)
    print(f"  {'Start Time':<22} {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"  {'Environment':<22}       {os.environ['ENVIRONMENT']}")
    print(f"  {'Encryption':<22}        {'Enabled' if int(os.environ['ENCRYPTED']) else 'Disabled'}")
    print(f"  {'MAX_PO_IN_FLIGHT':<22}  {os.environ['MAX_PO']}")
    print("═" * 46 + "\n")

# Start <Docker|Aster> based off the environment variable ENVIRONMENT.
def start():
    # Docker
    if os.environ['ENVIRONMENT']=='docker':
        # Create a subprocess that 
        p = subprocess.run(
        "py -3 build.py auto",
        shell=True,
        cwd='docker/',
        capture_output=True,
        text=True)
        # TO DO: check for subprocess success & run docker compose. Maybe a docker compose down first.  

    # Aster
    else:
        pass


# python3 run.py <docker|aster> <0|1> <MAX_PO_IN_FLIGHT> <NUM_REPLICAS>
#   <docker|aster>        :     Environment selection
#   <encrypted|plain>     :     Encrypted or unecrypted (spines)
#   <MAX_PO_IN_FLIGHT>    :     Max number of pre-order requests allowed in flight across Prime (must be >=1)
#   <NUM_REPLICAS>        :     Total number of replicas participating in Prime (must be >=6)
#
#
# environment variable ENVIRONMENT stores environment selection <docker|aster> as type str
# environment variable ENCRYPTED stores encryption selection  <0|1> as type str
# environment variable MAX_PO stores MAX_PO_IN_FLIGHT selection as type str
# environment variable NUM_REPLICAS stores NUM_REPLICAS selection as type str
def main():
    # clear terminal for readability
    subprocess.run('cls' if platform.system()=='Windows' else 'clear', shell=True)

    # get CLI arguments, confirm valid, store as environment variables & initialize UPDATED env var
    parse_cli(sys.argv)

    # Update the repo & store affected directories (if any) in environment variable 'UPDATED' for subsequent
    # rebuilds/remakes. Reboot the script in case of an update in order to use the most up to date version.
    
    # This only effects the local build. In the case of Aster, the remote machines execute their own 
    # updates IFF the UPDATE environment variable contains any directories. 
    update_repo()

    # Start either Docker or Aster based on process environment variable "ENVIRONMENT"
    start()

if __name__=="__main__":
    main()