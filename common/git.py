# Standard library imports
import os
import subprocess
import sys
import time
# Local imports
from .env_vars import get_env
from .error_handler import handle_error

# Updates the CS2910 repository on the machine the calling
# script is running on. If an update is detected, reboot the 
# calling script to have the most up to date version of CS2910.
def update_repo():
    # The 'UPDATE' environment variable is only created when
    # this function executes an update. If it exists then
    # do nothing (the update has already been applied & 
    # calling script rebooted), otherwise check for an 
    # update. 

    # Does not exist, no update has occurred, check for updates.
    if not get_env('UPDATED'):
        # Update the git repo, cwd should already be CS2910
        print("Checking for updates in CS2910 repository...")
        # Spawn a subprocess that executes the update, its 
        # output is then analyzed to check if one has occurred 
        # and track any modified directories. 
        p = subprocess.run(
            ["git","pull"],
            text=True,
            capture_output=True
        )
        # Proceed if no errors, otherwise handle the error
        if p.returncode==0:
            # Check if update occurred, record the names of all the top level
            # directories included in the update (if it occurred) in the environment
            # variable UPDATED

            # update has occurred. 
            if updated_directories():
                # Reboot the calling script
                reboot()
            # no update
            else:
                print('No updates detected, using the most up to date version.')
        # Error, pass the subprocess's stderr
        else:
            handle_error('git.py',p.stderr)
    # Update applied, do nothing and return
    else:
        return

# Stores the names of all the top level directories
# affected by the recent updated in the environment 
# varable 'UPDATED' as a comma separated string. 
# 
# Returns:
#   True: an update has occurred
#   False: an update has not occurred
def updated_directories():
    # Get the changes made to the repo
    p = subprocess.run(
    ["git", "diff", "--name-only", "ORIG_HEAD", "HEAD"],
    capture_output=True,
    text=True
    )
    # Subprocess executed successfully
    if p.returncode==0:
        # No updates, return 0
        if not p.stdout:
            return False
        # Updates occurred, record impacted directories & return 1
        else:
            # Store the names of each unique top level directories affected by the 
            # update in the environment variable UPDATED 
            # example output of subprocess:
            #   prime/src/driver.c
            #   spines/example/example.h 
            #   .....
            # Below would set the environment variable UPDATED to string 'prime,spines'
            os.environ['UPDATED'] = ','.join(set(line.split('/')[0] for line in p.stdout.splitlines()))
            return True
    # Subprocess encountered errors
    else:
        handle_error('git.py',p.stderr)


# Reboot the calling script
# test_mode used for quicker testing, reboot time becomes 0
def reboot(test_mode:bool=False):
    # Create & set the REBOOT env variable to 1
    os.environ['REBOOT']='1'
    reboot_time = 3 if not test_mode else 0
    # Print reboot msg
    for i in range(reboot_time, 0, -1):
        print(f"\rUpdate detected & applied, rebooting in {i} seconds...", end="", flush=True)
        time.sleep(1)
    # additional spaces
    print("\rUpdate applied. Restarting script...                 ", flush=True)    
    # On Windows use subprocess to resolve console formatting bug - child reboots and 
    # parent exits, child takes over, fixes powershell output bug
    if os.name == "nt":
        subprocess.run([sys.executable] + sys.argv)
        sys.exit(0)
    else:
        os.execv(sys.executable, [sys.executable] + sys.argv)

