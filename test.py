

# python run.py -e aster1 -x plain -p 100 -r 8 -f off -d 1

import sys, subprocess, time, os
from pathlib import Path
from datetime import datetime

def main():

    num_trials = 3
    max_po_list = [20, 100, 500, 1000]
    emulated_list = [20, 100, 500, 750]
    updates=25000
    filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    for num_replicas in [6, 8]:
        for encrypted in ['encrypted', 'plain']:
            for distribution in [1]:
                    for max_po in max_po_list:
                        subprocess.run([
                        sys.executable, "run.py",
                        "-e", "aster1",
                        "-x", encrypted,
                        "-p", str(max_po),
                        "-r", str(num_replicas),
                        "-f", "off",
                        "-d", str(distribution)
                    ], check=True)
                        elapsed = 0
                        stalls = 0
                        actual = 0
                        avg_latency = 0
                        min_latency = 0
                        max_latency = 0
                        for emulated_client in emulated_list:
                            elapsed = 0
                            stalls = 0
                            actual = 0
                            avg_latency = 0
                            min_latency = 0
                            max_latency = 0

                            for trial in range(1, num_trials + 1):
                                result = subprocess.run(
                                    [
                                        "ssh", "-T", "sjl79@aster17.cs.pitt.edu",
                                        f"cd ~/cs2910/prime/bin && "
                                        f"./driver -l 192.168.53.26 -i 1 -s 7 "
                                        f"-c {updates} -n {emulated_client}"
                                    ],
                                    capture_output=True,
                                    text=True,
                                    check=False
                                )

                                print("ERROR:", result.stderr)
                                print("OUTPUT:", result.stdout)
                                fields = next(line.split(",") for line in result.stdout.splitlines()
                                            if line.startswith("RESULT,"))

                                elapsed += float(fields[3])
                                stalls += int(fields[4])
                                actual += float(fields[6])
                                min_latency += float(fields[7])
                                max_latency += float(fields[8])
                                avg_latency += float(fields[9])

                            elapsed /= num_trials
                            stalls /= num_trials
                            actual /= num_trials
                            min_latency /= num_trials
                            max_latency /= num_trials
                            avg_latency /= num_trials


if __name__ == '__main__':
    main()
