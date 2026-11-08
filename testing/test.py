import sys
from pathlib import Path
import subprocess
import csv
import select
from time import sleep
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


from common.git import update_repo
from aster import aster_common
from common import threads 

# Structure: {total_replicas: {aster_machine_number: (replica_id, ip_address)}}
aster_config = {
    # 6 Total Replicas
    6: {
        # Aster 15, Replica ID 1, IP ADDR "192.168.53.24"
        15: (1, "192.168.53.24"),
        # Aster 16, Replica ID 2, IP ADDR "192.168.53.25"
        16: (2, "192.168.53.25"),
        # Aster 17, Replica ID 3, IP ADDR "192.168.53.26"
        17: (3, "192.168.53.26"),
        # Aster 18, Replica ID 4, IP ADDR "192.168.53.27"
        18: (4, "192.168.53.27"),
        # Aster 19, Replica ID 5, IP ADDR "192.168.53.28"
        19: (5, "192.168.53.28"),
        # Aster 20, Replica ID 6, IP ADDR "192.168.53.29"
        20: (6, "192.168.53.29"),
    },

    # 7 Total Replicas
    7: {
        # Aster 14, Replica ID 1, IP ADDR "192.168.53.23"
        14: (1, "192.168.53.23"),
        # Aster 15, Replica ID 2, IP ADDR "192.168.53.24"
        15: (2, "192.168.53.24"),
        # Aster 16, Replica ID 3, IP ADDR "192.168.53.25"
        16: (3, "192.168.53.25"),
        # Aster 17, Replica ID 4, IP ADDR "192.168.53.26"
        17: (4, "192.168.53.26"),
        # Aster 18, Replica ID 5, IP ADDR "192.168.53.27"
        18: (5, "192.168.53.27"),
        # Aster 19, Replica ID 6, IP ADDR "192.168.53.28"
        19: (6, "192.168.53.28"),
        # Aster 20, Replica ID 7, IP ADDR "192.168.53.29"
        20: (7, "192.168.53.29"),
    },

    # 8 Total Replicas
    8: {
        # Aster 13, Replica ID 1, IP ADDR "192.168.53.22"
        13: (1, "192.168.53.22"),
        # Aster 14, Replica ID 2, IP ADDR "192.168.53.23"
        14: (2, "192.168.53.23"),
        # Aster 15, Replica ID 3, IP ADDR "192.168.53.24"
        15: (3, "192.168.53.24"),
        # Aster 16, Replica ID 4, IP ADDR "192.168.53.25"
        16: (4, "192.168.53.25"),
        # Aster 17, Replica ID 5, IP ADDR "192.168.53.26"
        17: (5, "192.168.53.26"),
        # Aster 18, Replica ID 6, IP ADDR "192.168.53.27"
        18: (6, "192.168.53.27"),
        # Aster 19, Replica ID 7, IP ADDR "192.168.53.28"
        19: (7, "192.168.53.28"),
        # Aster 20, Replica ID 8, IP ADDR "192.168.53.29"
        20: (8, "192.168.53.29"),
    },

    # 9 Total Replicas
    9: {
        # Aster 12, Replica ID 1, IP ADDR "192.168.53.21"
        12: (1, "192.168.53.21"),
        # Aster 13, Replica ID 2, IP ADDR "192.168.53.22"
        13: (2, "192.168.53.22"),
        # Aster 14, Replica ID 3, IP ADDR "192.168.53.23"
        14: (3, "192.168.53.23"),
        # Aster 15, Replica ID 4, IP ADDR "192.168.53.24"
        15: (4, "192.168.53.24"),
        # Aster 16, Replica ID 5, IP ADDR "192.168.53.25"
        16: (5, "192.168.53.25"),
        # Aster 17, Replica ID 6, IP ADDR "192.168.53.26"
        17: (6, "192.168.53.26"),
        # Aster 18, Replica ID 7, IP ADDR "192.168.53.27"
        18: (7, "192.168.53.27"),
        # Aster 19, Replica ID 8, IP ADDR "192.168.53.28"
        19: (8, "192.168.53.28"),
        # Aster 20, Replica ID 9, IP ADDR "192.168.53.29"
        20: (9, "192.168.53.29"),
    },

    # 10 Total Replicas
    10: {
        # Aster 11, Replica ID 1, IP ADDR "192.168.53.20"
        11: (1, "192.168.53.20"),
        # Aster 12, Replica ID 2, IP ADDR "192.168.53.21"
        12: (2, "192.168.53.21"),
        # Aster 13, Replica ID 3, IP ADDR "192.168.53.22"
        13: (3, "192.168.53.22"),
        # Aster 14, Replica ID 4, IP ADDR "192.168.53.23"
        14: (4, "192.168.53.23"),
        # Aster 15, Replica ID 5, IP ADDR "192.168.53.24"
        15: (5, "192.168.53.24"),
        # Aster 16, Replica ID 6, IP ADDR "192.168.53.25"
        16: (6, "192.168.53.25"),
        # Aster 17, Replica ID 7, IP ADDR "192.168.53.26"
        17: (7, "192.168.53.26"),
        # Aster 18, Replica ID 8, IP ADDR "192.168.53.27"
        18: (8, "192.168.53.27"),
        # Aster 19, Replica ID 9, IP ADDR "192.168.53.28"
        19: (9, "192.168.53.28"),
        # Aster 20, Replica ID 10, IP ADDR "192.168.53.29"
        20: (10, "192.168.53.29"),
    },
}

METRIC_NAMES = [
    "total_updates",
    "elapsed",
    "throughput",
    "total_stalls",
    "min_latency",
    "max_latency",
    "avg_latency",
]

HEADERS = [
    "replicas", "encrypted", "max_po", "distribution",
    "emulated_clients", "num_trials",
    "mean_total_updates", "mean_elapsed", "mean_throughput",
    "mean_total_stalls", "mean_min_latency",
    "mean_max_latency", "mean_avg_latency",
]


# # # # # # # # # # # # # #  
# #{TEST CONFIGURATIONS}# #
# #   VARIABLES USED    # #
# #   & OTHER STUFF     # #
# # # # # # # # # # # # # #  
global total_replicas_used, spines_encryption_status, max_po_list, emulated_list,updates

# Total number of replicas being used in the test 
total_replicas_used = [6,7,8]
# Number of clients the driver program is emulating 
emulated_list = [20, 100, 500, 1000, 2500, 5000, 25000]
# Number of updates each driver program sends
updates = 25000
# Number of trials per test configuration
num_trials = 5 
# Spines encryption <disabled = 0, enabled = 1>
spines_encryption_status = [0,1]
# Maximum number of preorder requests Prime allows to be in flight simultaneously 
max_po_list = [20, 100, 500, 1000, 2500, 5000, 25000]

# List of all test configurations where each config is stored as a tuple
# Each tuple has the following ordering:    
#   [i][0] = max_po
#   [i][1] = replica_count
#   [i][2] = encryption_value
#   [i][3] = distribution (number of machines the updates are distributed across (i.e. num machines running the driver program)) 
#   [i][4] = number of clients to emulate 
all_test_configs = []
# TOTAL TESTS TO BE PERFORMED
all_test_count = 0

    # Dictionary that holds all SSH subprocesses 

'''
    DICTIONARY WHICH HOLDS THE SSH SUBPROCESSES THAT COMMUNICATE WITH ALL THE ASTER REPLICAS
    KEY = machine id, VALUE  = reference to ssh subprocess associated with that machine
'''
sessions = {}

'''
Generate all possible test configurations using the global variables:

(1) total_replicas_used
    - Prime: Modify def.h and config files, recompile and restart
    - Spines: Modify config files and restart

(2) max_po_list
    - Prime: Modify def.h, recompile and restart

(3) spines_encryption_status
    - Spines: Modify config files and restart
    - Prime: Restart to reestablish connections

(4) distribution
    - No file modifications or restarts required

(5) emulated_list
    - No file modifications or restarts required

The test variables are ordered to minimize restarts (config file changes)
and recompilations (def.h changes) to minimize testing time.
'''
def generate_all_test_configurations():
        for replica_count in total_replicas_used:
            for max_po in max_po_list:
                for encryption_value in spines_encryption_status:
                    for dist in range(1,replica_count+1):
                        for num_emulated in emulated_list:
                            all_test_configs.append((max_po, replica_count, encryption_value, dist, num_emulated))


'''
    Creates num_to_allocate SSH subprocesses where each 
    connects to its own distinct aster machine. 

    Returns a list of newly allocated machines (SSH subprocesses connected to those aster machines) 
'''
def allocate_machines(replica_count:int, curr_sessions:int, sessions:dict):
    
    # Update the machines_in_use global in aster_common
    aster_common.generate_machine_list(replica_count)
    
    # Start all the newly allocated machines & return the 
    # list of subprocesses associated with these machines 
    return aster_common.start_replicas(sessions)


'''
    Prints the current test information & replica status
'''
def print_status(curr_test: tuple, test_number: int, failure_count: int):
    print('\033[2J\033[H', end='')
    print('\n')
    print("=" * 48)
    print("              ASTER TESTING STATUS")
    print(f"                 TEST {test_number+1:,} OF {len(all_test_configs):,}")
    print(f"                 FAILURES: {failure_count:,}")
    print("=" * 48)
    print("  CURRENT CONFIGURATION")
    print("-" * 48)
    print(f"  MAX PO           : {curr_test[0]:,}")
    print(f"  Replicas         : {curr_test[1]}")
    print(f"  Encryption       : {'ENABLED' if curr_test[2] else 'DISABLED'}")
    print(f"  Distribution     : {curr_test[3]}")
    print(f"  Emulated Clients : {curr_test[4]:,}")
    print("=" * 48)
    print_replica_statuses(sessions)
'''
    Prints replica status 
'''
def print_replica_statuses(sessions: dict):
    active_threads = []

    for machine_id in sorted(sessions.keys()):
        process = sessions[machine_id]

        # Request current status from the current aster machine 
        aster_common.write_to_aster(process, "CURRENT_STATUS")

        # Create a separate thread that waits for a response 
        threads.add_thread( 
            active_threads, machine_id,
            aster_common.read_from_aster, process
        )

    # Waits for all threads assigned to each subprocess & stores 
    # results as results={machine_id:'Response'|None if none}
    results = threads.wait_for_threads(active_threads, timeout=3)

    for machine_id, response in sorted(results.items()):
        if not response:
            print(f"ASTER {machine_id}: No response")
            continue

        parts = response.strip().split(" | ")
        print(f"ASTER {machine_id}: {' | '.join(parts[:5])}")
        print(f"  {parts[6]}")
        print(f"  {parts[5]} | Driver Status: {parts[7].split(': ', 1)[1]}")
        print()

'''
    Runs each test configuration stored in all_test_configs
'''
def run_tests_aster():

    # Holds the previous test tuple configuration
    previous_test = None

    # Iterate through all test configurations & execute each one
    for test_number,current_test in enumerate(all_test_configs):
        # Set test parameters 
        max_po:int =                    current_test[0]
        replica_count:int =             current_test[1]
        encryption_status:int =         current_test[2]
        distribution:int =              current_test[3]
        num_clients_to_Emulate:int =    current_test[4]
        failures = 0 # num times this test has failed (disconnects, crashes, etc.)

        # Allocates more aster machines if sessions < replica_count
        if len(sessions)<replica_count: 
            allocate_machines(replica_count, len(sessions), sessions)

        # Output Status
        print_status(current_test, test_number,failures)


        # Setup the test - send the configuration information to each replica 
        active_threads=[]
        command = f"SETUP_TEST: {max_po} {replica_count} {encryption_status}"
        for machine_id, process in sorted(sessions.items()):
            threads.send_and_create_thread(
            active_threads,
            machine_id,
            process,
            command,
            aster_common.write_to_aster,
            aster_common.read_from_aster
        )

        # Thread Results
        results = threads.wait_for_threads(active_threads,timeout=30)
        for machine_id, response in sorted(results.items()):
            if not response:
                process = sessions[machine_id]
                print(f"ASTER {machine_id} STDERR:")
                print(process.stderr.read())
                raise RuntimeError(f"ASTER {machine_id}: No response")

        print_status(current_test, test_number,failures)
        sleep(5)
        # Handle Driver Assignment & execute test 

        exit(0)

def main():

    '''
        Get the most up to date CS2910 Github Repo. 
        The script will restart if an update is applied. 
    '''
    update_repo()

    '''
        Generate all test configurations (generate_all_test_configurations())
        and store them in all_test_count

        Get the total number of tests that will run & store this value in all_test_count
    '''
    global all_test_count
    generate_all_test_configurations()
    all_test_count = len(all_test_configs)*num_trials

    '''
        Run all test configurations in Aster
    '''
    run_tests_aster()


if __name__ == "__main__":
    try:
        main()
    finally:
        for process in sessions.values():
            process.stdin.write("disconnect\n")
            process.stdin.flush()


