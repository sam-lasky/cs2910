import sys, subprocess, time, os, socket, platform

def kill_all(sessions):
    if sessions is None:
        for i in range(13, 19):
            print(f"Cleaning Aster{i}...", flush=True)
            subprocess.run(
                [
                    "ssh",
                    f"sjl79@aster{i}.cs.pitt.edu",
                    "pkill -x prime; pkill -x spines"
                ],
                check=False
            )        
        return
    for i, process in sessions.items():
        # Kill Prime, Spines, and startup script on remote machine
        subprocess.run(
            [
                "ssh",
                f"sjl79@aster{i}.cs.pitt.edu",
                "pkill -x prime; pkill -x spines; pkill -f '[s]tartup_replica.py'"
            ],
            check=False
        )

        # Close local terminal window
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    # closes terminal windows
    sessions.clear()


def run_tests(sessions,max_po,encrypted):
    # link speed (Mbps) [where 0 is no limit]
    bandwidth = ['no_limit']
    # total updates sent from the driver program to prime
    total_updates = 25000
    # number of clients the driver program emulates 
    num_emulated = [20, 30, 50, 75, 100, 150, 200, 300, 500, 750]
    # num_emulated = [1,5,10,15,20,25,30,50,100]
    # number of trials
    num_trials = 3
    hosts = ['aster13','aster14','aster15','aster16','aster17','aster18']

    # clear previous terminal output b4 displaying results
    print("\033[2J\033[H", end="", flush=True)
    for speed in bandwidth:
        results_file = f"{speed}mbps_MAX_PO_{max_po}_ENCRYPTED_{encrypted}.txt"
        if speed!='no_limit':
            # can't modify link speeds on aster w/o sudo
            for i in range(13, 19):
                print(f"Configuring Aster{i} to {speed} Mbps...", flush=True)

                subprocess.run(
                    [
                        "ssh",
                        "-tt",
                        f"sjl79@aster{i}.cs.pitt.edu",
                        f"sudo tc qdisc replace dev eth0 root handle 1: htb default 10 && "
                        f"sudo tc class replace dev eth0 parent 1: classid 1:10 htb rate {speed}mbit"
                    ],
                    check=True
                )

        for clients in num_emulated:
            for i in range(1,num_trials+1):
                results = None
                print(f'Running trial {i}, Link Speed {speed}, Num Emulated {clients}, Max_PO {max_po}, Encrypted {encrypted}')
                # driver only running on replica 13
                results = subprocess.run(
                    [
                        "ssh",
                        "sjl79@aster13.cs.pitt.edu",
                        f"cd ~/cs2910/prime/bin && "
                        f"./driver -l 192.168.53.22 -i 1 -s 1 "
                        f"-c {total_updates} -n {clients}"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                filtered = "*** Test Results" + results.stdout.split("*** Test Results", 1)[-1]

                print(filtered, flush=True)

                with open(results_file, "a") as f:
                    f.write(filtered + "\n")

def main():
    # get max po
    max_po = sys.argv[1]
    # get encrypted status
    encrypted = sys.argv[2]
    
    # clear terminal for easier readabilityd
    clear_cmd = 'cls' if platform.system()=='Windows' else 'clear'
    subprocess.run(clear_cmd, shell=True)
    print(f"In the Windows Aster Controller, using MAX_PO_IN_FLIGHT {max_po}...")
    # Kill any existing replica startup scripts
    print("Terminating any existing Prime and Spines processes on Aster machines...", flush=True)    
    kill_all(None)

    # Start new sessions
    sessions = {}
    id =1
    for i in range(13, 19):
        print(f'Starting session with Aster {i}')
        sessions[i] = subprocess.Popen(
            f'ssh sjl79@aster{i}.cs.pitt.edu '
            f'"output=$(git -C cs2910 pull 2>&1 || git clone https://github.com/sam444555/cs2910.git 2>&1); '
            f'echo \\"$output\\"; '
            f'cd cs2910/aster && '
            f'python3 -u startup_replica.py {id} {max_po} {encrypted} \\"$output\\""',
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        id+=1

    # wait for replicas to initialize
    print("Waiting 60 seconds for replicas to initialize...", flush=True)
    time.sleep(60)
    # run tests
    run_tests(sessions, max_po, encrypted)
    # wait 10 secs 
    print("Waiting 10 seconds before cleanup...", flush=True)
    time.sleep(10)
    # terminate all sessions 
    kill_all(sessions)


if __name__=='__main__':
    main()