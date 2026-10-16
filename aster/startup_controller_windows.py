import sys, subprocess, time, os, socket

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
    # //closes terminal windows
    sessions.clear()


def run_tests(sessions):
    # link speed (Mbps) [where 0 is no limit]
    bandwidth = [0]
    # total updates sent from the driver program to prime
    total_updates = 25000
    # number of clients the driver program emulates 
    num_emulated = [1,5,10,15,20,25,30,50,100]
    # number of trials
    num_trials = 5

    # clear previous terminal output b4 displaying results
    print("\033[2J\033[H", end="", flush=True)
    for speed in bandwidth:
        results_file = f"{speed}mbps.txt"
        processes=[]
        if speed > 0:
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
            #     processes.append(p)

            # for p in processes:
            #     if p.wait() !=0:
            #         raise RuntimeError(f"Failed setting up bandwidth of {speed} Mbps")

        for clients in num_emulated:
            for i in range(1,num_trials+1):
                results = None
                print(f'Running trial {i}, Link Speed {speed}, Num Emulated {clients}')
                # driver only running on replica 13
                results = subprocess.run(
                    [
                        "ssh",
                        "sjl79@aster13.cs.pitt.edu",
                        f"cd ~/cs2910/prime/bin && "
                        f"./driver -l 192.168.53.22 -i 1 -s 1 "
                        f"-c {total_updates} -n {clients} -LS {speed} -trialnum {i}"
                    ],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(results.stdout, flush=True)

                with open(results_file, "a") as f:
                    f.write(results.stdout)


def main():
    print("In the Windows Aster Controller...")
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
            f'python3 -u startup_replica.py {id} \\"$output\\""',
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        id+=1
    next_step = input('\nNext Choice: Kill all Sessions | Run tests:\n>>')
    # stops all the processes on the aster machines and closes all the terminal windows locally
    if next_step=='kill':
        kill_all(sessions)
    elif next_step=='test':
        run_tests(sessions)

if __name__=='__main__':
    main()