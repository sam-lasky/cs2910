# std lib imports
import os
import platform
import subprocess
import sys
from datetime import datetime
import argparse
# local imports 
from common.git import update_repo
from aster import aster_local_controller
from docker import docker_local_controller

# Usage:
# python3 run.py -e <docker|aster_LAN_1|aster_LAN_2> -x <0|1> -p <MAX_PO_IN_FLIGHT> -r <NUM_REPLICAS> -f <on|off>
#
#   -e  Environment                 : docker, aster_LAN_1, or aster_LAN_2
#   -x  Encryption (Spines)         : 0 (plain text) or 1 (encrypted)
#   -p  MAX_PO_IN_FLIGHT            : Maximum number of pre-order requests in flight (integer > 0)
#   -r  NUM_REPLICAS                : Total number of Prime replicas (integer > 0)
#   -f  Patch                       : 0 (disabled) or 1 (enabled) ***OPTIONAL***
# All flags are required, unless explicitly labeled as optional, to run this script.            

def main():

    # The environment variable UPDATE does not exist yet. It is only created 
    # when a reboot occurs. A reboot has not occurred, run the standard setup
    # procedure. 
    if 'REBOOT' not in os.environ:
        # CLEAR THE TERMINAL
        print('\033[2J\033[H', end='')
        # CHECK FOR UPDATES 
        update_repo()

    # A reboot has occurred. The reboot func os.execv() preserves environment variables. 
    # Skip previous, delete the REBOOT environment variable and print reboot success 
    else:
        # Delete the REBOOT environment variable so child processes do not 
        # mistakenly use it when running their own updates upon inheriting it
        del os.environ['REBOOT']
        print('Script restarted successfully. Now using most up to date CS2910 repository.')
        print(f'Affected Directories/Files: {os.environ['UPDATED']}')

    # Parse CLI arguments and store them in a dictionary:
    # {
    #     'env': 'docker' | 'aster_LAN_1' | 'aster_LAN_2',
    #     'encrypt': 0 | 1,
    #     'max_po': int,
    #     'num_replicas': int,
    #     'initial': 0 | 1
    # }
    args_dict = parse_args()


    # If aster start the local controller & pass args_dict 
    if args_dict['env'] in ['aster_LAN_1','aster_LAN_2']:
        aster_local_controller.run(args_dict)
    # Docker
    # else:
    #     print('TODO: FINISH DOCKER')
    #     exit(0)




def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", dest="env", type=str, required=True)
    parser.add_argument("-x", dest="encrypt", type=int, required=True)
    parser.add_argument("-p", dest="max_po", type=int, required=True)
    parser.add_argument("-r", dest="num_replicas", type=int, required=True)
    parser.add_argument("-i", dest="initial", type=int, required=True)

    return vars(parser.parse_args())


if __name__=="__main__":
    main()





