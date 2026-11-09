
import sys
import subprocess
import time
import os
import threading
# local 
sys.path.insert(0, "..")
from common.spines_manager import *
from common.prime_manager import *
from aster_common import EXPECTED_ASTER_RESPONSES, generate_machine_list

# * * * ** * * ** * * * *
# * * * * GLOBALS * * * *
# * * * ** * * ** * * * *


# Unique integer identifier of the Replica 
local_replica_id = None
# Unique integer identifer of the Aster Machine
aster_machine_id = None
# Total # of replicas being used
num_replicas = None
# Assume Aster_1_LAN in all cases (for now, TODO: EXPAND TO ALL ENVs)
env = 'aster_LAN_1'
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
    global local_replica_id
    # 53 if LAN_1, 54 if LAN_2
    LAN = '53' if env == 'aster_LAN_1' else '54'
    for replica_id, (aster_id, _) in enumerate(generate_machine_list(num_replicas),start=1):
            id_to_ip[replica_id]=f'192.168.{LAN}.{aster_id+9}'
            if aster_id==aster_machine_id:
                local_replica_id=replica_id

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
    # Update id_to_ip mapping [replica ID -> IP address].
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

    if (make_count_prime ==0) or( num_replicas != old_num_replicas):
        rebuild_prime = True
        restart_prime = True
        configure_spines = True
        restart_spines = True

    if max_po != old_max_po:
        rebuild_prime = True
        restart_prime = True

    if encrypt != old_encrypt:
        configure_spines = True
        restart_spines = True
        restart_prime = True

    # SETUP SPINES!
    if configure_spines:
        setup_spines(id_to_ip, encrypt)

    # START SPINES! (start spines exits out the curr spines process & starts it up again)
    if restart_spines:
        start_spines(id_to_ip, local_replica_id)

    # SETUP PRIME!
    if rebuild_prime:
        setup_and_build_prime(id_to_ip, num_replicas, max_po)
        make_count_prime+=1

    # START PRIME! (start prime exits out the curr prime process & starts it up again)
    if restart_prime:
        start_prime(id_to_ip, local_replica_id)


'''
    Runs the driver process on this replica 
  Alarm(PRINT, "Usage: ./client\n"
      "\t -l IP (A.B.C.D)\n"
      "\t -c count_of_transactions_to_benchmark\n"
      "\t -i client_id, indexed base 1\n"
      "\t[-s server_id, indexed base 1]\n"
      "\t[-n num_clients_to_emulate]\n"
      "\t[-r num_prime_replicas]\n"
  );
'''
def run_driver(updates:int, num_clients:int):
    kill_driver(wait_time=1)
    my_ip = id_to_ip[local_replica_id]
    driver_command =(
        f"./driver -l {my_ip} "
        f"-c {updates} "
        f"-i {local_replica_id} "
        f"-s {local_replica_id} "
        f"-n {num_clients} "
        f"-r {num_replicas}"
    )
    driver_subprocess = subprocess.Popen(
        driver_command.split(),
        cwd="../prime/bin",
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return driver_subprocess

# Reads the driver's output (thread)
def read_driver_output(process, state):
    for line in process.stdout:
        if line.startswith("Highest SeqNo Processed="):
            state["progress"] = line.strip()
        elif line.startswith("RESULT,"):
            state["result"] = line.strip()


def main(machine_id_arg: int):
    # Update globals with passed args 
    global aster_machine_id, assigned_driver
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

    # driver subprocess reference
    driver_process = None
    driver_state = {"progress": None, "result": None}

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
            result = driver_state["result"]
            driver_status = "FINISHED" if result else (driver_state["progress"] or "N/A")
            response = (
                f"Replica ID: {local_replica_id} | "
                f"Aster Machine: {aster_machine_id} | "
                f"Total Replicas: {num_replicas} | "
                f"Encryption: {encrypt} | "
                f"MAX PO: {max_po} | "
                f"Assigned Driver: {assigned_driver} | "
                f"Active Processes: {get_active_processes().strip()} | "
                f"Driver Output: {driver_status} | Driver Result: {result or ''}"
            )
        # Sets up the test environment (Spines/Prime)
        elif command.startswith('SETUP_TEST:'):
            # Reset driver data
            assigned_driver=False
            driver_state = {"progress": None, "result": None}
            set_up_test_env(*map(int, command.split(':', 1)[1].split()))
            response='READY'
        # Run the driver program on this replica: passed as DRIVER <TOTAL_UPDATES>
        elif command.startswith('DRIVER '):
            assigned_driver=True # this rep was assigned a driver process 
            _,updates,num_clients = command.split()
            driver_process=run_driver(int(updates), int(num_clients))
            driver_state = {"progress": None, "result": None}
            threading.Thread(
                target=read_driver_output,
                args=(driver_process, driver_state),
                daemon=True,
            ).start()
            response='DRIVER STARTED'

    
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
