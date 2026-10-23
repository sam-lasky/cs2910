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



def main():
    print('[Aster Controller Local]')
    exit(0)
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


