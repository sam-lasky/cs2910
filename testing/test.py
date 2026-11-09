import sys
from pathlib import Path
import subprocess
import csv
import select
import math
import os
from time import sleep,monotonic
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
num_trials = 3 
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
    Stores the results for each replica running a driver program. 
    driver_results[machine_id]['progress'] stores the most up to date progress output from the driver program
    driver_results[machine_id]['results'] stores the results once the driver program concludes 
'''
driver_results={}
'''
    final_results[test_key][trial_num] stores all the results for the current trial (across all driver program result data)
    and averages them out & stores them in the results file once trial_num == num_trials
'''
final_results={}

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
def print_status(curr_test: tuple, test_number: int, failure_count: int, trial_num:int,total_trials:int,updates_per_driver):

    # Windows: CLEAR TERMINAL 
    if os.name=="nt":
        os.system("cls")
    # Mac/Linux: CLEAR TERMINAL
    else:
        print("\033[2J\033[H", end="", flush=True)
    
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
    print(f"  Current Trial:   : {trial_num}/{total_trials}")
    print("=" * 48)
    print_replica_statuses(sessions,updates_per_driver)
'''
    Prints replica status 
'''
def print_replica_statuses(sessions: dict,updates_per_driver):
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
        status, _, result = response.partition(" | Driver Result: ")
        result = result.strip()
        if result:
            driver_results[machine_id] = result

        parts = status.strip().split(" | ")
        print(f"ASTER {machine_id}: {' | '.join(parts[:5])}")
        print(f"  {parts[6]}")
        print(f"  {parts[5]} | Driver Status: {parts[7].split(': ', 1)[1]}")
        _, _, count = parts[7].partition("Total Updates Processed=")
        if count and updates_per_driver:
            completed = int(count.split()[0])
            print(f"  TEST STATUS = {completed:,}/{updates_per_driver:,} ({completed / updates_per_driver:.1%})")
        print()


'''
    Handles a given test config's output 
    test_confgig =(max_po, replica_count,encryption_status,distribution,num_clients_to_Emulate,trial_num,failures)

    results = 
        # [0] "RESULT",
        # [1] Elapsed time (seconds),
        # [2] Send stalls,
        # [3] Expected throughput (updates/sec),
        # [4] Actual throughput (updates/sec),
        # [5] Minimum latency (ms),
        # [6] Maximum latency (ms),
        # [7] Average latency (ms),
        # [8] Start timestamp,
        # [9] End timestamp

'''
def handle_output(test_config,min_test_time,total_num_trials,driver_ids):
    (max_po, 
     replica_count,
     encryption_status,distribution,
     num_clients_to_Emulate,
     trial_num,
     updates)=test_config

    # key = machine_id, val = dict{....}
    driver_results_by_machine = {}

    # Go through the results, parse each machines output and store it in driver_results_by_machine 
    for machine_id in driver_ids:
        result = driver_results[machine_id]
        fields= result.split(",")
        print(f"Trial {trial_num} | ASTER {machine_id} | start={fields[8]} | end={fields[9]}")
        # input("Press enter to continue...")
        elapsed_seconds = float(fields[1])

        # test failed to exceed threshold 
        if elapsed_seconds<min_test_time:
            return False, elapsed_seconds

        # store the driver results for each machine 
        driver_results_by_machine[machine_id] = {
            'elapsed_time':elapsed_seconds, 
            'send_stalls':int(fields[2]),   
            'expected_tp':float(fields[3]), 
            'actual_tp':float(fields[4]),   
            'min_lat':float(fields[5]),
            'max_lat':float(fields[6]),
            'avg_lat':float(fields[7]),
            'start_ts':float(fields[8]),
            'end_ts':float(fields[9])
        }

    # Total number of participating drivers
    total_drivers = len(driver_results_by_machine.keys())

    # Total number of updates = passed updates 
    # Store final results 
    test_key = (max_po,replica_count, encryption_status,distribution,num_clients_to_Emulate)
    mean_elapsed_time_secs= 0 
    mean_send_stalls = 0
    mean_min_lat = 0
    mean_max_lat = 0
    mean_avg_lat = 0

    latest_driver_endtime = 0
    earliest_driver_start_time = float("inf")
    
    for machine_id in sorted(driver_results_by_machine.keys()):
        mean_elapsed_time_secs+=    driver_results_by_machine[machine_id]['elapsed_time']
        mean_send_stalls+=          driver_results_by_machine[machine_id]['send_stalls']
        mean_min_lat +=             driver_results_by_machine[machine_id]['min_lat']
        mean_max_lat +=             driver_results_by_machine[machine_id]['max_lat']
        mean_avg_lat +=             driver_results_by_machine[machine_id]['avg_lat'] 

        start_time = driver_results_by_machine[machine_id]['start_ts']
        end_time = driver_results_by_machine[machine_id]['end_ts']

        earliest_driver_start_time = min(earliest_driver_start_time, start_time)
        latest_driver_endtime = max(latest_driver_endtime, end_time)


    mean_elapsed_time_secs /= total_drivers
    mean_send_stalls /= total_drivers
    mean_min_lat /= total_drivers
    mean_max_lat /= total_drivers
    mean_avg_lat /= total_drivers

    overall_elapsed_time = latest_driver_endtime - earliest_driver_start_time
    overall_tp = updates / overall_elapsed_time

    final_results.setdefault(test_key, {})[trial_num] = {
        "total_updates": updates,
        "overall_elapsed_time": overall_elapsed_time,
        "overall_tp": overall_tp,
        "mean_send_stalls": mean_send_stalls,
        "mean_min_lat": mean_min_lat,
        "mean_max_lat": mean_max_lat,
        "mean_avg_lat": mean_avg_lat,
    }
        
    trials = final_results[test_key]

    if len(trials) == num_trials:
        with open(f"results/{replica_count}_results.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            csv_row = [
                    *test_key,
                    sum(row["total_updates"] for row in trials.values()),
                    sum(row["overall_elapsed_time"] for row in trials.values()),
                    sum(row["overall_tp"] for row in trials.values()) / num_trials,
                    sum(row["mean_send_stalls"] for row in trials.values()) / num_trials,
                    sum(row["mean_min_lat"] for row in trials.values()) / num_trials,
                    sum(row["mean_max_lat"] for row in trials.values()) / num_trials,
                    sum(row["mean_avg_lat"] for row in trials.values()) / num_trials,
                ]

            if file.tell() == 0:

     
                writer.writerow([
                    "max_po",
                    "replica_count",
                    "encryption_status",
                    "distribution",
                    "emulated_clients_per_driver",
                    "total_updates",
                    "total_elapsed_seconds",
                    "mean_throughput_updates_per_sec",
                    "mean_send_stalls",
                    "mean_min_latency_ms",
                    "mean_max_latency_ms",
                    "mean_avg_latency_ms",
                ])

            writer.writerow(csv_row)

        # mark this config as completed to avoid redundant test configs 
        with open("results/completed_configs.txt", "a", encoding="utf-8") as file:
                file.write(
                    f"{max_po},{replica_count},{encryption_status},"
                    f"{distribution},{num_clients_to_Emulate}\n"
                )
    else:
        # mark this trial as completed to avoid redundant trial runs 
        with open("results/completed_trials.txt", "a", encoding="utf-8") as file:
            file.write(
                f"{max_po},{replica_count},{encryption_status},"
                f"{distribution},{num_clients_to_Emulate},{trial_num}\n"
            )

    return True,None 

def load_completed():
    # all completed trials as a set 
    try:
        with open("results/completed_trials.txt", encoding="utf-8") as file:
            completed_trials = {
                tuple(map(int, line.strip().split(",")))
                for line in file
                if line.strip()
            }
    except FileNotFoundError:
        completed_trials = set()

    # all completed tests configs as a set 
    try:
        with open("results/completed_configs.txt", encoding="utf-8") as file:
            completed_configs = {
                tuple(map(int, line.strip().split(",")))
                for line in file
                if line.strip()
            }
    except FileNotFoundError:
        completed_configs = set()

    return completed_trials,completed_configs

'''
    Runs each test configuration stored in all_test_configs
'''
def run_tests_aster():

    completed_trials,completed_configs = load_completed()

    # Minimum amount of time a test needs to take. If the test does not meet
    # this threshold, dynamic_updates is adjusted & the test gets rerun
    # using this update value until it meets the threshold. 
    min_test_time = 15 #seconds

    # Holds the test success results, if true ignore msg otherwise
    # store the cause as the msg
    test_sucessful = [False,'Failure_Msg if False']

    # Iterate through all test configurations & execute each one
    for test_number,current_test in enumerate(all_test_configs):
        # Unpack the curr test tuple
        (
            max_po,
            replica_count,
            encryption_status,
            distribution,
            num_clients_to_Emulate
        ) = current_test

        # Test config already complete & test config written, skip 
        if current_test in completed_configs:
            continue

        # The number of updates get scaled up if the current test configuration fails 
        # to meet the time threshold 
        dynamic_updates = updates

        # Trial counter for current config
        trial_num = 1

        # Number of failures experienced by this config
        failures = 0

        # Allocates more aster machines if sessions < replica_count
        if len(sessions)<replica_count: 
            allocate_machines(replica_count, len(sessions), sessions)


        while trial_num<=num_trials or not test_sucessful[0]:
            # TODO: IMPLEMENT THIS trial ahs already executed, skip it and update trial num
            # if (*current_test, trial_num) in completed_trials:
            #     trial_num += 1
            #     continue
            test_sucessful=[False, 'JUST STARTED'] #RESET

            # Output Status
            # print_status(current_test, test_number,failures)

            # Setup the test - send the configuration information to each replica, print all replica statuses if successful
            command=f"SETUP_TEST: {max_po} {replica_count} {encryption_status}"
            send_command_to_replicas(sessions,command,timeout=30, distribution=len(sessions.keys()))
            print_status(current_test, test_number,failures,trial_num,num_trials,dynamic_updates//distribution)
            print("\nREPLICAS ARE CURRENTLY SETTING UP THE TEST ENVIRONMENT....")

            '''
                EXECUTE: Starting at the aster machine number (ascending), distribute the update

            '''
            # Get the machines that will be assigned a driver prog 
            driver_ids = sorted(sessions)[:distribution]
            driver_sessions = {machine_id: sessions[machine_id] for machine_id in driver_ids}
            # DRIVER <NUM_UPDATES> <NUM_CLIENTS_TO_EMULATE>
            command=f"DRIVER {dynamic_updates//distribution} {num_clients_to_Emulate}"
            send_command_to_replicas(driver_sessions,command,timeout=5, distribution=len(driver_sessions))
            driver_results.clear() # RESET

            # 2 min timeout 
            deadline = monotonic() + 120

            # Print status of all replicas every 2 seconds during the test
            # 2 minute timeout, if exceeded break & repeat test 
            while True:
                print_status(current_test, test_number,failures,trial_num,num_trials,dynamic_updates//distribution)
                if all(machine_id in driver_results for machine_id in driver_ids):
                    test_sucessful[0]=True
                    break
                if monotonic() >=deadline:
                    test_sucessful[1]='TIMEOUT'
                    failures+=1
                    break
                sleep(2)    

            # Test successful, handle the output
            if test_sucessful[0]:
                test_config =(max_po, replica_count,encryption_status,distribution,num_clients_to_Emulate,trial_num,dynamic_updates)
                # time threshold met 
                success, test_time = handle_output(test_config, min_test_time, num_trials,driver_ids)
                if success: trial_num+=1
                # time threshold not met, discard results & scale up dynamic updates 
                else:
                    test_sucessful[0]=False                    
                    dynamic_updates = math.ceil(
                        dynamic_updates * min_test_time / test_time
                    )

'''
    Send the command to the aster machine(s). Create a thread for each machine being sent to. Returned 
    value is a dictionary results where key=replica id, val=response. If there is no response then an error
    is raised and the program terminates 
'''
def send_command_to_replicas(sessions:dict,command:str,timeout:float, distribution=len(sessions.keys())):
    # Stores all active threads 
    active_threads=[]

    # where machine_id ==> aster_id && process ==> the ssh subprocess communicating with that machine
    for machine_id, process in sorted(sessions.items()):
        # only issue commands to distribution # of machines
        if distribution:
            # Create a thread for this machine & issue the command 
            threads.send_and_create_thread(
            active_threads,
            machine_id,
            process,
            command,
            aster_common.write_to_aster,
            aster_common.read_from_aster
            )
            distribution-=1
        else: break

    # wait for threads 
    results = threads.wait_for_threads(active_threads,timeout=timeout)

    # check results & issue required errs 
    for machine_id, response in sorted(results.items()):
        if not response:
            process = sessions[machine_id]
            if process.poll() is not None and process.stderr is not None:
                print(f"ASTER {machine_id} STDERR:")
                print(process.stderr.read())
            raise RuntimeError(f"ASTER {machine_id} failed to reply to {command!r}")

    # ret
    return results

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


