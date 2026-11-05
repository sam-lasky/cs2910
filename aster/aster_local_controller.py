import sys, subprocess, time, os, socket, platform
from common.env_vars import store_env, get_env

# IDs of machines being used ([1,2,3] = aster1/2/3 being used)
aster_machines_used = []

'''
    args_dict{
        'env':                  <'aster_LAN_1' | 'aster_LAN_2',
        'encrypt':              < 0 | 1 >,
        'MAX_PO_IN_FLIGHT':     int value > 0,
        'NUM_REPLICAS':         int value > 0
    }

'''
def run(args_dict:dict):

    # List of aster machine IDs to skip
    # (Being used, do not work, etc.)
    skip=[3]

    # Clear the terminal for readability
    print('\033[2J\033[H', end='')

    '''
        STEP 1: GENERATE MACHINE LIST 

        There are 20 total aster machines. Generate the list of 
        machines that will be used starting at 20 and descending 
        until the machine list has num_replicas of elements
    '''
    generate_machine_list(args_dict['num_replicas'], skip)

    '''
        STEP 2: CONNECT TO THE ASTER MACHINES IN MACHINE LIST

            SSH into each Aster machine and perform the following:

            (2.B) In the home directory (/home/your_pitt_id), clone the CS2910
                GitHub repository if it does not already exist. Otherwise,
                update the existing repository to the latest version.

            (2.B) Launch aster_replica.py on the remote machine to configure
                and start Spines and Prime.

            Store each SSH subprocess in a dictionary, mapping the Aster
            machine name to its corresponding subprocess.Popen object.

            Return the dictionary so the caller can monitor the subprocesses
            and check their exit statuses.
    ''' 
    return start_replicas(args_dict)

    
    



# For all aster machines in aster_machines_used:
#   (1) Connect to the machine
#   (2) Clone or update cs2910 repo
#   (3) Launch aster_replica.py
def start_replicas(args_dict:dict):
    # Convert aster_machines_used from list to comma separated string to be passed to aster_replica.py
    aster_machines_used_as_str = ','.join(map(str, aster_machines_used))
    # Get the environment
    env = args_dict['env']
    # Get the max_po
    max_po = args_dict['max_po']
    # Get encrypted (0/1)
    encrypt = args_dict['encrypt']
    # Generate the argument list: 
    args_str = f"{aster_machines_used_as_str} {env} {max_po} {encrypt}" 
   
    # ssh sessions, session[i] = subprocess of aster machine i (where 1<=i<=20)
    sessions = {}
    # unique id of the replica
    id=1
    for aster_machine_id in aster_machines_used:
        # Updates the repo if it exists, otherwise clones it. 
        # Purges stdout/err by writing to dev/null
        git_command = (
            '{ if [ -d cs2910/.git ]; then '
            'git -C cs2910 pull; '
            'else git clone https://github.com/sam444555/cs2910.git; '
            'fi; } > /dev/null 2>&1 && '
        )
        # CD into aster dir and startup the replica startup script
        replica_startup_command = (
            'cd cs2910/aster && '
            f'python3 -u aster_replica.py {id} {aster_machine_id} {args_str}'
        )
        # ssh to the aster machine, run the above command
        sessions[aster_machine_id] = subprocess.Popen(
            ['ssh', '-T', f'sjl79@aster{aster_machine_id}.cs.pitt.edu',
            git_command + replica_startup_command],
            stdin=subprocess.PIPE,  
            stdout=subprocess.PIPE, 
            text=True,
            bufsize=1
        )
        id += 1

    return sessions

def generate_machine_list(num_replicas, skipped_machines):
    # Starting at machine 20, iterate backward and add each machine that is not in skipped_machines
    # until all num_replicas have been added to the global list aster_machines_used
    global aster_machines_used

    for i in range(20,0,-1):
        if i not in skipped_machines:
            aster_machines_used.append(i)
            if len(aster_machines_used)==num_replicas:
                # sort in ascending order
                aster_machines_used.sort()
                return
    # Too many skipped machines
    if len(aster_machines_used)<num_replicas:
        raise ValueError("Not enough machines available. Exiting.")

