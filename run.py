# std lib imports
import os
import platform
import subprocess
import sys
from datetime import datetime
# local imports 
from common.cli_parser import cli_parse_args
from common.git import update_repo
from common.env_vars import get_encryption_status
from aster import aster_local_controller


# Usage:
# python3 run.py -e <docker|aster> -x <encrypted|plain> -p <MAX_PO_IN_FLIGHT> -r <NUM_REPLICAS> -f <on|off>
#
#   -e  Environment       : docker or aster
#   -x  Encryption        : encrypted or plain (Spines)
#   -p  MAX_PO_IN_FLIGHT  : Maximum number of pre-order requests in flight (integer > 0)
#   -r  NUM_REPLICAS      : Total number of Prime replicas (integer > 0)
#   -f  Patch             : on or off
#
# Environment Variables:
#   ENVIRONMENT    : Environment selection (docker|aster), stored as str
#   ENCRYPTED      : Encryption selection (encrypted|plain), stored as str
#   MAX_PO         : MAX_PO_IN_FLIGHT value, stored as str
#   NUM_REPLICAS   : Replica count, stored as str
#   PATCH_APPLIED  : Patch selection (on|off), stored as str
#
# All five flags and associated values are required for this script to execute. 

def main():

    # The environment variable UPDATE does not exist yet. It is only created 
    # when a reboot occurs. A reboot has not occurred, run the standard setup. 
    if 'REBOOT' not in os.environ:
        # clear terminal for readability
        subprocess.run('cls' if platform.system()=='Windows' else 'clear', shell=True)

        # get CLI arguments, confirm valid, store as environment variables
        cli_parse_args(args=sys.argv, calling_script_name='run')

        # Output configuration to console
        print("\n" + "═" * 46)
        print("           STARTUP CONFIGURATION")
        print("═" * 46)
        print(f"  {'Start Time':<22} {datetime.now().strftime('%I:%M:%S %p')}")
        print(f"  {'Environment':<22} {os.environ['ENVIRONMENT']}")
        print(f"  {'Spines Encrypted':<22} {'Yes' if get_encryption_status() else 'No'}")
        print(f"  {'MAX_PO_IN_FLIGHT':<22} {os.environ['MAX_PO']}")
        print("═" * 46 + "\n")

        # update the CS2910 github repository.
        print('[CS2910 Git Repo Synchronization]')
        update_repo()

    # A reboot has occurred. The reboot func os.execv() preserves environment variables. 
    # Skip previous, delete the REBOOT environment variable and print reboot success 
    else:
        # Delete the REBOOT environment variable so child processes do not 
        # mistakenly use it when running their own updates
        del os.environ['REBOOT']
        print('Script restarted successfully. Now using most up to date CS2910 repository.\n')

    # Start the local controller based on ENVIRONMENT env var value <aster|docker>
    if os.environ['ENVIRONMENT']=='aster':
        aster_local_controller.main()
    else:
        print('TODO: INCORPORATE DOCKER SUPPORT')
        exit(0)









if __name__=="__main__":
    main()