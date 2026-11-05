import sys
from pathlib import Path
import subprocess
import csv
import select
from time import sleep

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


from datetime import datetime
from common.git import update_repo
from aster import aster_local_controller


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
# # TEST CONFIGURATIONS # #
# # # # # # # # # # # # # #  
global total_replicas_used, spines_encryption_status, max_po_list, emulated_list,updates

# Total number of replicas being used in the test 
total_replicas_used = [6,7,8]
# Number of clients the driver program is emulating 
emulated_list = [20, 100, 500, 1000, 2500, 5000, 25000]
# Number of updates each driver program sends
updates = 25000
# How many replicas the updates will be distributed across 
distribution = [1]
# Number of trials per test configuration
num_trials = 5 

def main():
    '''
        Get the most up to date CS2910 Github Repo. 
        The script will restart if an update is applied. 
    '''
    update_repo()

    '''
        Call the Aster local controller to start all replicas per num replicas with the initial test configuration.
        Retain the active SSH subprocesses to communicate with the replicas and modify Prime/Spines during testing.
    '''
    # for num_replicas in total_replicas_used:
    # Spines encryption <disabled = 0, enabled = 1>
    spines_encryption_status = [0,1]
    # Maximum number of preorder requests Prime allows to be in flight simultaneously 
    max_po_list = [20, 100, 500, 1000, 2500, 5000, 25000]

    sessions:dict = aster_local_controller.run(args_dict={
        'env':'aster_LAN_1',
        'encrypt':spines_encryption_status[0],
        'max_po':max_po_list[0],
        'num_replicas':6
    })

    status = {i:'Unknown' for i in range(1,7)}
    ready_count = 0
    while True:
        for machine, process in sessions.items():
            ready, _, _ = select.select([process.stdout], [], [], 0)
            if ready:
                status[machine]=process.stdout.readline().strip()

        print("\033[2J\033[H", end="", flush=True)
        printout=''
        for i in sorted(status.keys()):
            printout+=f"Aster {i} status: {status[i]}"
        print(printout)
        sleep(1)

    # print("Aster machines are starting up....")
    # for machine, process in sessions.items():
    #     while True:
    #         line = process.stdout.readline()

    #         if not line:
    #             raise RuntimeError(f"Aster {machine} disconnected")

    #         status = line.strip()

    #         if status == "READY":
    #             print(f"Aster {machine} is ready and awaiting input")
    #             break
    #         else: print(f"\rAster {machine}: {status}", end="", flush=True)
    # print("All machines are ready & are awaiting input...")



    # for machine, process in sessions.items():
    #     process.stdin.write("terminate\n")
    #     process.stdin.flush()

    # for machine, process in sessions.items():
    #     print(machine, process.stdout.readline().strip())
    #     print("Exit status:", process.wait(timeout=10))


        # # If aster start the local controller & pass args_dict 
    # if args_dict['env'] in ['aster_LAN_1','aster_LAN_2']:
    #     aster_local_controller.run(args_dict)





if __name__ == "__main__":
    main()






    
#     run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#     csv_file = f"throughput_results_{run_id}.csv"
#     with open(csv_file, "x", newline="") as f:
#         csv.writer(f).writerow(HEADERS)

#     for num_replicas in total_replicas_used:
#         for encrypted in encrypted_values:
#             for max_po in max_po_list:
#                 if num_replicas == 6 and encrypted == 0 and max_po == 20:
#                     print("Skipping completed replicas=6, MAX_PO=20", flush=True)
#                     continue

#                 for distribution in [1]:
#                     subprocess.run(
#                         [
#                             sys.executable, "../run.py",
#                             "-e", "aster_LAN_1",
#                             "-x", str(encrypted),
#                             "-p", str(max_po),
#                             "-r", str(num_replicas),
#                         ],
#                         check=True,
#                     )

#                     for emulated_client in emulated_list:
          
#                         trial_results = []
#                         min_test_seconds = 15

#                         for trial in range(1, num_trials + 1):
#                             machines = aster_config[num_replicas]
#                             updates_distributed = updates // distribution

#                             print_test_config(
#                                 num_replicas, encrypted, max_po,
#                                 distribution, emulated_client, trial,
#                                 num_trials, updates_distributed
#                             )

#                             while True:
#                                 processes = []

#                                 for key in sorted(
#                                     sorted(machines.keys(), reverse=True)[:distribution]
#                                 ):
#                                     print(f"starting driver on aster {key}")
#                                     driver_process = subprocess.Popen(
#                                         generate_command(
#                                             key, machines, num_replicas,
#                                             updates_distributed, emulated_client
#                                         ),
#                                         stdout=subprocess.PIPE,
#                                         stderr=subprocess.STDOUT,
#                                         text=True,
#                                     )
#                                     processes.append(driver_process)

#                                 results = []

#                                 for process in processes:
#                                     print("Waiting for driver...", flush=True)
#                                     output, _ = process.communicate()
#                                     print("Driver finished.", flush=True)

#                                     for line in output.splitlines():
#                                         if line.startswith("RESULT,"):
#                                             fields = line.split(",")
#                                             results.append({
#                                                 "clients": int(fields[1]),
#                                                 "updates": int(fields[2]),
#                                                 "elapsed": float(fields[3]),
#                                                 "stalls": int(fields[4]),
#                                                 "expected": float(fields[5]),
#                                                 "actual": float(fields[6]),
#                                                 "min": float(fields[7]),
#                                                 "max": float(fields[8]),
#                                                 "avg": float(fields[9]),
#                                                 "start": float(fields[10]),
#                                                 "end": float(fields[11]),
#                                             })

#                                 if len(results) != distribution:
#                                     raise RuntimeError(
#                                         "One or more drivers failed to return results"
#                                     )

#                                 elapsed = (
#                                     max(r["end"] for r in results)
#                                     - min(r["start"] for r in results)
#                                 )

#                                 if elapsed < min_test_seconds:
#                                     updates_distributed *= 2
#                                     print(
#                                         f"Trial {trial}: {elapsed:.2f}s "
#                                         f"< {min_test_seconds}s. Doubling updates "
#                                         f"to {updates_distributed} per driver.",
#                                         flush=True,
#                                     )
#                                     continue

#                                 total_updates = sum(r["updates"] for r in results)
#                                 if total_updates <= 0:
#                                     raise RuntimeError(
#                                         "Drivers reported no completed updates"
#                                     )

#                                 throughput = total_updates / elapsed
#                                 total_stalls = sum(r["stalls"] for r in results)
#                                 min_latency = min(r["min"] for r in results)
#                                 max_latency = max(r["max"] for r in results)
#                                 avg_latency = (
#                                     sum(r["avg"] * r["updates"] for r in results)
#                                     / total_updates
#                                 )

#                                 trial_results.append({
#                                     "total_updates": total_updates,
#                                     "elapsed": elapsed,
#                                     "throughput": throughput,
#                                     "total_stalls": total_stalls,
#                                     "min_latency": min_latency,
#                                     "max_latency": max_latency,
#                                     "avg_latency": avg_latency,
#                                 })

#                                 print(
#                                     f"Finished trial {trial}: "
#                                     f"{throughput:.2f} updates/sec",
#                                     flush=True,
#                                 )
#                                 break

#                         averages = {
#                             name: sum(r[name] for r in trial_results)
#                             / len(trial_results)
#                             for name in METRIC_NAMES
#                         }

#                         with open(csv_file, "a", newline="") as f:
#                             csv.writer(f).writerow([
#                                 num_replicas,
#                                 encrypted,
#                                 max_po,
#                                 distribution,
#                                 emulated_client,
#                                 len(trial_results),
#                                 *[averages[name] for name in METRIC_NAMES],
#                             ])

#                         print(
#                             f"Saved average of {len(trial_results)} trials: "
#                             f"{averages['throughput']:.2f} updates/sec",
#                             flush=True,
#                         )

#         print(
#             f"Completed {num_replicas} replicas. Results saved to: {csv_file}",
#             flush=True,
#         )


# def print_test_config(
#     num_replicas, encrypted, max_po, distribution,
#     emulated_client, trial, num_trials, updates_distributed
# ):
#     print(
#         f"\n[TEST CONFIG] "
#         f"Replicas={num_replicas} | "
#         f"Encrypted={encrypted} | "
#         f"MAX_PO={max_po} | "
#         f"Distribution={distribution} | "
#         f"Emulated Clients={emulated_client} | "
#         f"Trial={trial}/{num_trials} | "
#         f"Updates per Driver={updates_distributed}",
#         flush=True,
#     )

# '''
#     Driver Usage: ./client"
#         -l IP (A.B.C.D)
#             >> IP address 
#         -c count_of_transactions_to_benchmark
#         -i client_id, indexed base 1
#         -s server_id, indexed base 1
#         -n num_clients_to_emulate]
#         -r num_prime_replicas
# '''
# def generate_command(key, machines, num_replicas, updates_distributed, emulated_client):
#     return [
#         # sh command
#         "ssh",
#         # aster server being ssh'd into
#         f"sjl79@aster{key}.cs.pitt.edu",
#         # Go to the directory of the driver executable
#         f"cd ~/cs2910/prime/bin"
#         f"exec ./driver -l {machines[key][1]} "
#         f"-i {machines[key][0]} "
#         f"-s {machines[key][0]} "
#         f"-r {num_replicas} "
#         f"-c {updates_distributed} "
#         f"-n {emulated_client}",
#     ]
