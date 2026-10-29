# std lib imports
import os
import platform
import subprocess
import sys
from datetime import datetime
# local imports 
from common.cli_parser import cli_parse_args
from common.git import update_repo
from aster import aster_local_controller


# Usage:
# python3 run.py -e <docker|aster_LAN_1|aster_LAN_2> -x <0|1> -p <MAX_PO_IN_FLIGHT> -r <NUM_REPLICAS> -f <on|off>
#
#   -e  Environment                 : docker, aster_LAN_1, or aster_LAN_2
#   -x  Encryption (Spines)         : 0 (plain text) or 1 (encrypted)
#   -p  MAX_PO_IN_FLIGHT            : Maximum number of pre-order requests in flight (integer > 0)
#   -r  NUM_REPLICAS                : Total number of Prime replicas (integer > 0)
#   -f  Patch                       : 0 (disabled) or 1 (enabled) ***OPTIONAL***
#
# All flags are required, unless explicitly labeled as optional, to run this script. 
def main():

    # The environment variable UPDATE does not exist yet. It is only created 
    # when a reboot occurs. A reboot has not occurred, run the standard setup
    # procedure. 
    if 'REBOOT' not in os.environ:
        # clear terminal for readability
        subprocess.run('cls' if platform.system()=='Windows' else 'clear', shell=True)

        # Updates the >>local<< CS2910 github repository.
        print("\n" + "═" * 46)
        print("           CS2910 Git Repo Synchronization")
        print("═" * 46)
        print('[]')
        update_repo()

    # A reboot has occurred. The reboot func os.execv() preserves environment variables. 
    # Skip previous, delete the REBOOT environment variable and print reboot success 
    else:
        # Delete the REBOOT environment variable so child processes do not 
        # mistakenly use it when running their own updates upon inheriting it
        del os.environ['REBOOT']
        print('Script restarted successfully. Now using most up to date CS2910 repository.')
        print(f'Affected Directories:{os.environ['UPDATED']}')

    # Using most up to date local CS2910 Github Repository. Parse the CLI arguments & store
    # them in the dictionary args_dict (keys:'env', 'encrypt', 'max_po', 'num_replicas', 'patch' (optional))
    args_dict=cli_parse_args(args=sys.argv, calling_script_name='run')

    # Print the configuration
    print_config(args_dict)
    # Start the local controller & pass args_dict 
    # Aster
    if args_dict['env'] in ['aster_LAN_1','aster_LAN_2']:
        aster_local_controller.run(args_dict)
    # Docker
    else:
        print('TODO: INCORPORATE DOCKER SUPPORT')
        exit(0)


def print_config(args_dict:dict):
    # Output configuration to console
    print("\n" + "═" * 46)
    print("           STARTUP CONFIGURATION")
    print("═" * 46)
    print(f"  {'Start Time':<22} {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"  {'Environment':<22} {args_dict['env']}")
    print(f"  {'Spines Encrypted':<22} {'YES' if args_dict['encrypt'] else 'NO'}")
    print(f"  {'MAX_PO_IN_FLIGHT':<22} {args_dict['max_po']}")
    print("═" * 46 + "\n")

if __name__=="__main__":
    main()





