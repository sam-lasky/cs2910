import csv
import subprocess
import sys
from datetime import datetime

aster_config = {6: {15: (1, '192.168.53.24'), 16: (2, '192.168.53.25'), 17: (3, '192.168.53.26'), 18: (4, '192.168.53.27'), 19: (5, '192.168.53.28'), 20: (6, '192.168.53.29')}, 7: {14: (1, '192.168.53.23'), 15: (2, '192.168.53.24'), 16: (3, '192.168.53.25'), 17: (4, '192.168.53.26'), 18: (5, '192.168.53.27'), 19: (6, '192.168.53.28'), 20: (7, '192.168.53.29')}, 8: {13: (1, '192.168.53.22'), 14: (2, '192.168.53.23'), 15: (3, '192.168.53.24'), 16: (4, '192.168.53.25'), 17: (5, '192.168.53.26'), 18: (6, '192.168.53.27'), 19: (7, '192.168.53.28'), 20: (8, '192.168.53.29')}, 9: {12: (1, '192.168.53.21'), 13: (2, '192.168.53.22'), 14: (3, '192.168.53.23'), 15: (4, '192.168.53.24'), 16: (5, '192.168.53.25'), 17: (6, '192.168.53.26'), 18: (7, '192.168.53.27'), 19: (8, '192.168.53.28'), 20: (9, '192.168.53.29')}, 10: {11: (1, '192.168.53.20'), 12: (2, '192.168.53.21'), 13: (3, '192.168.53.22'), 14: (4, '192.168.53.23'), 15: (5, '192.168.53.24'), 16: (6, '192.168.53.25'), 17: (7, '192.168.53.26'), 18: (8, '192.168.53.27'), 19: (9, '192.168.53.28'), 20: (10, '192.168.53.29')}}

COMPLETED_CONFIGS = {
    (6, 0, 20, distribution, clients)
    for distribution in (1, 3, 6)
    for clients in (20, 100, 500, 1000, 2500, 5000, 25000)
}

METRIC_NAMES = [
    "total_updates", "elapsed", "throughput", "total_stalls",
    "min_latency", "max_latency", "avg_latency",
]

HEADERS = [
    "replicas", "encrypted", "max_po", "distribution", "emulated_clients",
    "num_trials", *["mean_" + name for name in METRIC_NAMES],
]


def should_skip(num_replicas, encrypted, max_po, distribution, emulated_client):
    config = (num_replicas, encrypted, max_po, distribution, emulated_client)
    if config not in COMPLETED_CONFIGS:
        return False
    print(f"Skipping completed config: {config}", flush=True)
    return True


def create_csv(run_id, num_replicas):
    csv_file = f"throughput_results_{run_id}_replicas_{num_replicas}.csv"
    with open(csv_file, "x", newline="") as f:
        csv.writer(f).writerow(HEADERS)
    print(f"Writing results to {csv_file}", flush=True)
    return csv_file


def start_replicas(num_replicas, encrypted, max_po):
    subprocess.run([sys.executable, '../run.py', '-e', 'aster_LAN_1', '-x', str(encrypted), '-p', str(max_po), '-r', str(num_replicas)], check=True)

def launch_drivers(num_replicas, distribution, emulated_client, updates_distributed):
    machines = aster_config[num_replicas]
    processes = []
    for key in sorted(sorted(machines.keys(), reverse=True)[:distribution]):
        print(f'starting driver on aster {key}')
        driver_process = subprocess.Popen(['ssh', '-n', '-T', '-o', 'BatchMode=yes', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2', '-vv', '-E', f'ssh_aster{key}.log', f'sjl79@aster{key}.cs.pitt.edu', f'cd ~/cs2910/prime/bin && ./driver -l {machines[key][1]} -i {machines[key][0]} -s {machines[key][0]} -r {num_replicas} -c {updates_distributed} -n {emulated_client}'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        processes.append(driver_process)
    return processes

def collect_results(processes, distribution):
    results = []
    for process in processes:
        print('Waiting for driver...', flush=True)
        output, _ = process.communicate()
        print('Driver finished.', flush=True)
        for line in output.splitlines():
            if line.startswith('RESULT,'):
                fields = line.split(',')
                results.append({'clients': int(fields[1]), 'updates': int(fields[2]), 'elapsed': float(fields[3]), 'stalls': int(fields[4]), 'expected': float(fields[5]), 'actual': float(fields[6]), 'min': float(fields[7]), 'max': float(fields[8]), 'avg': float(fields[9]), 'start': float(fields[10]), 'end': float(fields[11])})
    if len(results) != distribution:
        raise RuntimeError('One or more drivers failed to return results')
    return results

def calculate_metrics(results, elapsed):
    total_updates = sum((r['updates'] for r in results))
    if total_updates <= 0:
        raise RuntimeError('Drivers reported no completed updates')
    throughput = total_updates / elapsed
    total_stalls = sum((r['stalls'] for r in results))
    min_latency = min((r['min'] for r in results))
    max_latency = max((r['max'] for r in results))
    avg_latency = sum((r['avg'] * r['updates'] for r in results)) / total_updates
    return {"total_updates": total_updates, "elapsed": elapsed, "throughput": throughput, "total_stalls": total_stalls, "min_latency": min_latency, "max_latency": max_latency, "avg_latency": avg_latency}

def run_trial(num_replicas, encrypted, max_po, distribution,
              emulated_client, trial, num_trials, updates, min_test_seconds):
    updates_distributed = updates // distribution
    print(
        f"\n[TEST CONFIG] Replicas={num_replicas} | Encrypted={encrypted} | "
        f"MAX_PO={max_po} | Distribution={distribution} | "
        f"Emulated Clients={emulated_client} | Trial={trial}/{num_trials}",
        flush=True,
    )
    while True:
        processes = launch_drivers(
            num_replicas, distribution, emulated_client, updates_distributed
        )
        results = collect_results(processes, distribution)
        elapsed = max(r["end"] for r in results) - min(r["start"] for r in results)
        if elapsed < min_test_seconds:
            updates_distributed *= 2
            print(
                f"Trial {trial}: {elapsed:.2f}s < {min_test_seconds}s. "
                f"Doubling updates to {updates_distributed} per driver.",
                flush=True,
            )
            continue
        metrics = calculate_metrics(results, elapsed)
        print(
            f"Finished trial {trial}: {metrics['throughput']:.2f} updates/sec",
            flush=True,
        )
        return metrics


def save_averages(csv_file, config, trial_results):
    averages = [
        sum(result[name] for result in trial_results) / len(trial_results)
        for name in METRIC_NAMES
    ]
    with open(csv_file, "a", newline="") as f:
        csv.writer(f).writerow([*config, len(trial_results), *averages])
    print(
        f"Saved average of {len(trial_results)} trials: "
        f"{averages[2]:.2f} updates/sec to {csv_file}",
        flush=True,
    )


def run_configuration(csv_file, config, num_trials, updates, min_test_seconds):
    trial_results = [
        run_trial(*config, trial, num_trials, updates, min_test_seconds)
        for trial in range(1, num_trials + 1)
    ]
    save_averages(csv_file, config, trial_results)


def main():
    num_trials = 2
    max_po_list = [20, 100, 500, 1000, 2500, 5000, 25000]
    total_replicas_used = [6, 8, 10]
    emulated_list = [20, 100, 500, 1000, 2500, 5000, 25000]
    encryption_settings = [0]
    updates = 25000
    min_test_seconds = 15
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    for num_replicas in total_replicas_used:
        csv_file = create_csv(run_id, num_replicas)
        for encrypted in encryption_settings:
            for max_po in max_po_list:
                for distribution in (num_replicas, num_replicas // 2, 1):
                    start_replicas(num_replicas, encrypted, max_po)
                    for emulated_client in emulated_list:
                        config = (
                            num_replicas, encrypted, max_po,
                            distribution, emulated_client,
                        )
                        if should_skip(*config):
                            continue
                        run_configuration(
                            csv_file, config, num_trials, updates, min_test_seconds
                        )
        print(
            f"Completed {num_replicas} replicas. Ready to analyze: {csv_file}",
            flush=True,
        )


if __name__ == "__main__":
    main()
