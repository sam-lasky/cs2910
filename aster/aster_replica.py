
import sys
import subprocess
import time
import os
# local 
sys.path.insert(0, "..")
from common.spines_manager import *
from common.prime_manager import *
from aster_common import EXPECTED_ASTER_RESPONSES, generate_machine_list

# * * * ** * * ** * * * *
# * * * * GLOBALS * * * *
# * * * ** * * ** * * * *

''' REPLICA ID AND MACHINE ID ARE IDENTICAL
        E.G if replica_id=x then aster_machine_id=x
        for sanity and consistency purposes 
'''
# Unique integer identifier of the Replica 
replica_id = None
# Unique integer identifer of the Aster Machine
aster_machine_id = None
# Total # of replicas being used
num_replicas = None
# Assume Aster_1_LAN in all cases (for now, TODO: EXPAND TO ALL ENVs)
env = 'Aster_1_LAN'
# MAX_PO_IN_FLIGHT (prime/src/def.h)
max_po = None
# Encrypted or Plain (prime/spines/daemon/spines.conf, IT_LinkCrypto, IT_LinkEncrypt)
encrypt = None
# Assigned a driver (yes/no)
assigned_driver=False
# k,v = REPLICA id (int), replica ip (str)
id_to_ip={}
# Tracks make counts (spines/prime) initialized to 0
make_count_prime = 0
# Driver program output
driver_out = None

# Populates the id_to_ip dictionary where the >> REPLICA ID<< is passed as the
# key and its IP is assigned as the value 
def build_id_to_ip_map():
    # 53 if LAN_1, 54 if LAN_2
    LAN = '53' if env == 'aster_LAN_1' else '54'
    for aster_id in generate_machine_list(num_replicas):
            id_to_ip[aster_id]=f'192.168.{LAN}.{aster_id+9}'

'''
    Kills any leftover driver processes on the replica, waits
    for wait_time before returning control in order to avoid 
    buggy behavior if the caller attempts to run drive directly
    after
'''
def kill_driver(wait_time):
    subprocess.run(["pkill", "-x", "driver"], check=False)
    time.sleep(wait_time)

'''
    Kills all processes on the replica 
'''
def kill_all(wait_time:float):
    kill_driver(wait_time=0)
    kill_spines(wait_time=0)
    kill_prime(wait_time=0)
    time.sleep(wait_time)


'''
    Spawns a subprocess on the replica that checks if the
    prime, spines and driver processes are running
'''
def get_active_processes():
    active_processes = ""
    for process_name in ['spines', 'prime', 'driver']:
        result = subprocess.run(["pgrep", "-x", process_name], capture_output=True)
        active_processes += f"[{process_name.capitalize()}]: {'Running' if result.returncode == 0 else 'None'}, "
    return active_processes.rstrip(", ")


'''
    Sets up the environment for the current testing configuration
'''
def set_up_test_env(passed_po:int, passed_rep_count:int, passed_encrypt:int):
    global max_po, num_replicas, encrypt, make_count_prime, make_count_spines
    # Preserve old global values 
    old_max_po = max_po
    old_num_replicas = num_replicas
    old_encrypt = encrypt
    # Update globals to reflect current test config 
    max_po = passed_po
    num_replicas=passed_rep_count
    encrypt=passed_encrypt
    # Update id_to_ip mapping [machine/replica ID -> IP address].
    # Uses generate_machine_list() which produces the same machine list on every replica
    # when given the same num_replicas value
    build_id_to_ip_map()
    # All possibilties actions
    #   Note: Spines only needs to be made once regardless of what changes. This is handled by default when the first setup_spines is 
    #   run which checks if Spines has already been made, otherwise it makes it. 
    rebuild_prime = False
    configure_spines = False
    restart_prime = False
    restart_spines = False

    if make_count_prime == 0:
        rebuild_prime = True
        restart_prime = True
        configure_spines = True
        restart_spines = True

    if max_po != old_max_po:
        rebuild_prime = True
        restart_prime = True

    if num_replicas != old_num_replicas:
        rebuild_prime = True
        configure_spines = True
        restart_prime = True
        restart_spines = True

    if encrypt != old_encrypt:
        configure_spines = True
        restart_spines = True
        restart_prime = True

    # SETUP SPINES!
    if configure_spines:
        setup_spines(id_to_ip, encrypt)

    # START SPINES! (start spines exits out the curr spines process & starts it up again)
    if restart_spines:
        start_spines(id_to_ip, replica_id)

    # SETUP PRIME!
    if rebuild_prime:
        setup_and_build_prime(id_to_ip, num_replicas, max_po)

    # START PRIME! (start prime exits out the curr prime process & starts it up again)
    if restart_prime:
        start_prime(id_to_ip, replica_id)


def main(machine_id_arg: int):
    '''
        Update globals. Replica & Machine id are set to the same value
        for simplicity. 
    '''
    global replica_id, aster_machine_id
    replica_id = machine_id_arg
    aster_machine_id = machine_id_arg

    '''
        [STEP 1] As soon as the replica launches, terminate 
        any leftover Driver/Spines/Prime processes from previous
        runs 
    '''
    wait_time = 0.5 # time the kill method waits until it returns 
    kill_all(wait_time)

    '''
        [STEP 2] Listen for commands from test.py & respond accordingly (as described beneath)

        EXPECTED COMMANDS: 
        (1) 'STARTUP_STATUS':['READY']
        (2) 'CURRENT_STATUS': returns the replica's machine status 
        (3) 'SETUP_FOR_TEST': gets passed all the info for the test & sets up
        Prime and Spines accordingly

    '''
    for command in sys.stdin:
        # remove whitespace
        command = command.strip()
        # response
        response = None

        # STARTUP_STATUS
        if command == 'STARTUP_STATUS':
            response=EXPECTED_ASTER_RESPONSES[command][0]
        # CURRENT_STATUS
        elif command == 'CURRENT_STATUS':
            '''
                Gets replica id, aster machine id, total replicas, encryption setting,
                MAX_PO setting, assigned driver (Yes/No) ,all active processes, 
            '''
            response = (
                f"Replica ID: {replica_id} | "
                f"Aster Machine: {aster_machine_id} | "
                f"Total Replicas: {num_replicas} | "
                f"Encryption: {encrypt} | "
                f"MAX PO: {max_po} | "
                f"Assigned Driver: {assigned_driver} | "
                f"Active Processes: {get_active_processes().strip()} | "
                f"Driver Output: {driver_out if assigned_driver else 'N/A'}"
            )
        # Sets up the test environment (Spines/Prime)
        elif command.startswith('SETUP_TEST:'):
            set_up_test_env(*map(int, command.split(':', 1)[1].split()))
            response='READY'

        # Print response (Written to stdout, read by SSH subprocess, flush so immediate)
        print(response,flush=True)

    
'''
    python aster_replica <machine_id:int> <num_replicas:int>
'''
if __name__ == "__main__":
    try:
        main(int(sys.argv[1]))
    finally:
        # << CLEANUP >> 
        # kills all active processes on this replica before exiting
        kill_all(wait_time=0)





  # # <--- Set up global variables --->
    # global replica_id, aster_machine_id, aster_machines_used, env, max_po, encrypt
    # # Integer (>0) that uniquely identifies the replica
    # replica_id =                int(sys.argv[1])
    # # Integer (1-->20) that uniquely identifies the aster machine
    # aster_machine_id =          int(sys.argv[2])
    # # List of aster ID's being used
    # aster_machines_used =       list(map(int, sys.argv[3].split(',')))
    # # Environment (aster LAN 1 | aster LAN 2)
    # env =                       sys.argv[4]
    # # Max preorder requests in flight (prime/src/def.h)
    # max_po =                    int(sys.argv[5])
    # # Spines encryption (enabled=1, disabled=0)
    # encrypt =                   int(sys.argv[6])

    # # Build the aster machine id <--> replica ip mapping
    # build_id_to_ip_map()
    # print("Setting up Spines...",flush=True)

    # # Sets up Spines
    # setup_spines(id_to_ip,encrypt)
    # print("Setting up Prime...",flush=True)

    # # Set up Prime
    # setup_prime(id_to_ip,num_replicas=len(id_to_ip.keys()),max_po=max_po)
    # print("Starting up Spines...",flush=True)

    # # Start Spines
    # start_spines(id_to_ip, replica_id)
    # print("Starting up Prime...",flush=True)
    
    # # Start Prime
    # start_prime(id_to_ip, replica_id)
    # print("READY",flush=True)

    # kill_prime()
    # kill_spines()
    # kill_driver()
    # exit(0)