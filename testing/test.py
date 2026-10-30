
import sys, subprocess, time, os
import csv
from pathlib import Path
from datetime import datetime
import time

# Structure: {total_replicas: {aster_machine_number: (replica_id, ip_address)}}
# Use the machine number for SSH (e.g., aster20).
# Use replica_id for BOTH driver flags -i and -s, and ip_address for -l.
# Example: with 6 replicas, Aster 20 is replica 6 → SSH to aster20, pass -i 6 -s 6.
aster_config = {
    6: {

        15: (1, "192.168.53.24"),
        16: (2, "192.168.53.25"),
        17: (3, "192.168.53.26"),
        18: (4, "192.168.53.27"),
        19: (5, "192.168.53.28"),
        20: (6, "192.168.53.29"),
    },
    7: {
        14: (1, "192.168.53.23"),
        15: (2, "192.168.53.24"),
        16: (3, "192.168.53.25"),
        17: (4, "192.168.53.26"),
        18: (5, "192.168.53.27"),
        19: (6, "192.168.53.28"),
        20: (7, "192.168.53.29"),
    },
    8: {
        13: (1, "192.168.53.22"),
        14: (2, "192.168.53.23"),
        15: (3, "192.168.53.24"),
        16: (4, "192.168.53.25"),
        17: (5, "192.168.53.26"),
        18: (6, "192.168.53.27"),
        19: (7, "192.168.53.28"),
        20: (8, "192.168.53.29"),
    },
    9: {
        12: (1, "192.168.53.21"),
        13: (2, "192.168.53.22"),
        14: (3, "192.168.53.23"),
        15: (4, "192.168.53.24"),
        16: (5, "192.168.53.25"),
        17: (6, "192.168.53.26"),
        18: (7, "192.168.53.27"),
        19: (8, "192.168.53.28"),
        20: (9, "192.168.53.29"),
    },
    10: {
        11: (1, "192.168.53.20"),
        12: (2, "192.168.53.21"),
        13: (3, "192.168.53.22"),
        14: (4, "192.168.53.23"),
        15: (5, "192.168.53.24"),
        16: (6, "192.168.53.25"),
        17: (7, "192.168.53.26"),
        18: (8, "192.168.53.27"),
        19: (9, "192.168.53.28"),
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
    "avg_latency"
]


HEADERS = [
    "replicas", "encrypted", "max_po", "distribution",
    "emulated_clients", "num_trials",
    "mean_total_updates", "mean_elapsed", "mean_throughput",
    "mean_total_stalls", "mean_min_latency",
    "mean_max_latency", "mean_avg_latency"
]


def main():

    # Total number of trials each test configuration runs 
    num_trials = 1
    # MAX_PO_IN_FLIGHT values tested (prime/src/def.h)
    max_po_list = [20, 100, 500, 1000, 2500, 5000, 25000]
    # Number of Replicas tested (NUM_SERVERS=(3*NUM_F + 2*NUM_K + 1) in prime/src/def.h)
    total_replicas_used = [6, 8, 10]
    # Number of emulated clients (prime/src/driver.c)
    emulated_list = [20, 100, 500, 1000, 2500, 5000, 25000]
    # Encrypted Status (0=False,1=True)
    encrypted = [0]
    
    # Total updates sent per individual test
    updates=25000
     

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # Test diff num of replicas [6, 8, 10]
    for num_replicas in total_replicas_used:
        csv_file = f"throughput_results_{run_id}_replicas_{num_replicas}.csv"
        with open(csv_file, "x", newline="") as f:
            csv.writer(f).writerow(HEADERS)
        # print(f"Writing results to {csv_file}", flush=True)
        # Test encrypted [0=True,1=False]
        for encrypted in [0]:
            # Test different MAX_PO values
            for max_po in max_po_list:
                # Distribution (Number of replicas running drivers, each assigned an equal share of total updates)
                for distribution in [num_replicas, num_replicas // 2, 1]:
                    # Execute run which runs num_replicas aster machines where each machine
                    # is using the current encryption status and max_po value 
                    subprocess.run([
                        sys.executable, "../run.py",
                        "-e", "aster_LAN_1",
                        "-x", str(encrypted),
                        "-p", str(max_po),
                        "-r", str(num_replicas) ]
                        , check=True)
    
                    # Test out different emulated client values in driver.c
                    for emulated_client in emulated_list:
                        # Skip all 21 completed configurations.
                        if should_skip( num_replicas, encrypted, max_po, distribution, emulated_client):continue
                        # Conduct num_trials of the current configuration.
                        trial_results = []
                        min_test_seconds = 15
                        for trial in range(1, num_trials + 1):
                            machines = aster_config[num_replicas]
                            updates_distributed = updates // distribution

                            # Prints the current test configuration
                            print_test_config(num_replicas, encrypted, max_po, distribution, emulated_client, trial, num_trials, updates_distributed)
    
                            while True:
                                processes = []

                                for key in sorted(sorted(machines.keys(), reverse=True)[:distribution]):
                                    print(f'starting driver on aster {key}')
                                    driver_process = subprocess.Popen(
                                    [
                                        "ssh",
                                        "-n",
                                        "-T",
                                        "-o", "BatchMode=yes",
                                        "-o", "ServerAliveInterval=15",
                                        "-o", "ServerAliveCountMax=2",
                                        "-vv",
                                        "-E", f"ssh_aster{key}.log",
                                        f"sjl79@aster{key}.cs.pitt.edu",
                                        f"cd ~/cs2910/prime/bin && "
                                        f"./driver -l {machines[key][1]} "
                                        f"-i {machines[key][0]} "
                                        f"-s {machines[key][0]} "
                                        f"-r {num_replicas} "
                                        f"-c {updates_distributed} "
                                        f"-n {emulated_client}"
                                    ],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True
                                    )
                                    processes.append(driver_process)

                                results = []

                                for process in processes:
                                    print("Waiting for driver...", flush=True)
                                    output, _ = process.communicate()
                                    print("Driver finished.", flush=True)

                                    for line in output.splitlines():
                                        if line.startswith("RESULT,"):
                                            fields = line.split(",")

                                            results.append({
                                                "clients": int(fields[1]),
                                                "updates": int(fields[2]),
                                                "elapsed": float(fields[3]),
                                                "stalls": int(fields[4]),
                                                "expected": float(fields[5]),
                                                "actual": float(fields[6]),
                                                "min": float(fields[7]),
                                                "max": float(fields[8]),
                                                "avg": float(fields[9]),
                                                "start": float(fields[10]),
                                                "end": float(fields[11])
                                            })

                                if len(results) != distribution:
                                    raise RuntimeError(
                                        "One or more drivers failed to return results"
                                    )

                                elapsed = (
                                    max(r["end"] for r in results)
                                    - min(r["start"] for r in results)
                                )

                                if elapsed < min_test_seconds:
                                    updates_distributed *= 2
                                    print(
                                        f"Trial {trial}: {elapsed:.2f}s "
                                        f"< {min_test_seconds}s. Doubling updates "
                                        f"to {updates_distributed} per driver.",
                                        flush=True
                                    )
                                    continue

                                total_updates = sum(r["updates"] for r in results)

                                if total_updates <= 0:
                                    raise RuntimeError(
                                        "Drivers reported no completed updates"
                                    )

                                throughput = total_updates / elapsed
                                total_stalls = sum(r["stalls"] for r in results)
                                min_latency = min(r["min"] for r in results)
                                max_latency = max(r["max"] for r in results)
                                avg_latency = (
                                    sum(r["avg"] * r["updates"] for r in results)
                                    / total_updates
                                )

                                trial_results.append({
                                    "total_updates": total_updates,
                                    "elapsed": elapsed,
                                    "throughput": throughput,
                                    "total_stalls": total_stalls,
                                    "min_latency": min_latency,
                                    "max_latency": max_latency,
                                    "avg_latency": avg_latency
                                })

                                print(
                                    f"Finished trial {trial}: "
                                    f"{throughput:.2f} updates/sec",
                                    flush=True
                                )
                                break



                        averages = {
                            name: sum(r[name] for r in trial_results)
                            / len(trial_results)
                            for name in METRIC_NAMES
                        }

                        with open(csv_file, "a", newline="") as f:
                            csv.writer(f).writerow([
                                num_replicas,
                                encrypted,
                                max_po,
                                distribution,
                                emulated_client,
                                len(trial_results),
                                *[averages[name] for name in METRIC_NAMES]
                            ])

                        print(
                            f"Saved average of {len(trial_results)} trials: "
                            f"{averages['throughput']:.2f} updates/sec",
                            flush=True
                        )
        print(
            f"Completed {num_replicas} replicas. Ready to analyze: {csv_file}",
            flush=True
        )


def print_test_config(
    num_replicas, encrypted, max_po, distribution,
    emulated_client, trial, num_trials, updates_distributed):    
    print(
            f"\n[TEST CONFIG] "
            f"Replicas={num_replicas} | "
            f"Encrypted={encrypted} | "
            f"MAX_PO={max_po} | "
            f"Distribution={distribution} | "
            f"Emulated Clients={emulated_client} | "
            f"Trial={trial}/{num_trials} | "
            f"Updates per Driver={updates_distributed}",
            flush=True
        )


def should_skip(num_replicas, encrypted, max_po, distribution, emulated_client):
    if (
        num_replicas == 6
        and encrypted == 0
        and max_po == 20
        and distribution in (1, 3, 6)
        and emulated_client in (20, 100, 500, 1000, 2500, 5000, 25000)
    ):
        print(
            f"Skipping completed config: replicas={num_replicas}, "
            f"MAX_PO={max_po}, distribution={distribution}, "
            f"clients={emulated_client}",
            flush=True
        )
        return True

    return False

if __name__ == '__main__':
    main()
