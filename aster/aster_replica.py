
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
make_count_spines, make_count_prime = 0,0
# Driver program output
driver_out = None

# Populates the id_to_ip dictionary where the >> REPLICA ID<< is passed as the
# key and its IP is assigned as the value 
def build_id_to_ip_map():
    # 53 if LAN_1, 54 if LAN_2
    LAN = '53' if env == 'aster_LAN_1' else '54'
    for i,aster_id in enumerate(generate_machine_list(num_replicas),start=1):
        id_to_ip[i]=f'192.168.{LAN}.{aster_id+9}'

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
        active_processes += f"{process_name.capitalize()}: {'Running' if result.returncode == 0 else 'None'} | "
    return active_processes.rstrip(" |")

def main(machine_id_arg: int, num_replicas_arg: int):
    '''
        Update globals. Replica & Machine id are set to the same value
        for simplicity. 
    '''
    global replica_id, aster_machine_id, num_replicas
    replica_id = machine_id_arg
    aster_machine_id = machine_id_arg
    num_replicas = num_replicas_arg

    '''
        [STEP 1] As soon as the replica launches, terminate 
        any leftover Driver/Spines/Prime processes from previous
        runs 
    '''
    wait_time = 0 # time the kill method waits until it returns 
    kill_all(wait_time)

    '''
        [STEP 2] Listen for commands from test.py & respond accordingly (as described beneath)

        EXPECTED COMMANDS: 
        (1) 'STARTUP_STATUS':['READY']
        (2) 

    '''
    for command in sys.stdin:
        # remove whitespace
        command = command.strip()
        # response
        response = None

        # STARTUP_STATUS
        if command == 'STARTUP_STATUS':
            response=EXPECTED_ASTER_RESPONSES[command][0]

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

        # Print response (Written to stdout, read by SSH subprocess, flush so immediate)
        print(response,flush=True)

    

'''
    python aster_replica <machine_id:int> <num_replicas:int>
'''
if __name__ == "__main__":
    try:
        main(int(sys.argv[1]), int(sys.argv[2]))
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