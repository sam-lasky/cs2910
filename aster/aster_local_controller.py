import sys, subprocess, time, os, socket, platform
from common.env_vars import store_env, get_env

# IDs of machines being used ([1,2,3] = aster1/2/3 being used)
aster_machines_used = []

# Kills any leftover prime, spines or aster_replica processes contained in 
# the machine list
def kill_all():
    print('\n[KILLING EXISTING PROCESSES]')
    for m in aster_machines_used.keys():
        print(f"Cleaning Aster{m}...", flush=True)
        subprocess.run(
            [
                "ssh",
                f"sjl79@aster{m}.cs.pitt.edu",
                "pkill -x prime; pkill -x spines; pkill -f '[a]ster_replica.py'"
            ],
            check=False
        )


# For all aster machines in aster_machines_used:
#   (1) Connect to the machine
#   (2) Clone or update cs2910 repo
#   (3) Launch aster_replica.py
def start_replicas():

    # Package all required environment variables so remote Aster replicas receive controller's configuration
    # Format: "ASTER_MACHINES_USED=<value> ENVIRONMENT=<value> MAX_PO=<value> ENCRYPTED=<value>"
    env_list = " ".join(f"{key}={os.environ[key]}" for key in ("ASTER_MACHINES_USED", "ENVIRONMENT", "MAX_PO", "ENCRYPTED"))

    # ssh sessions, session[i] = subprocess of aster machine i (where 1<=i<=20)
    sessions = {}
    # unique id of the replica
    id=1
    print('\n[STARTING MACHINES]')
    for machine_id in aster_machines_used:
        print(f'Starting session with Aster {machine_id}')
        # Update the remote repository and start the replica with its ID, machine ID, and environment variables
        # command = (
        #     f'git -C cs2910 pull && '
        #     f'cd cs2910/aster && '
        #     f'python3 -u aster_replica.py {id} {machine_id} {env_list}'
        # )
        # suppress git msgs 
        command = (
            f'git -C cs2910 pull > /dev/null 2>&1 && '
            f'cd cs2910/aster && '
            f'python3 -u aster_replica.py {id} {machine_id} {env_list}'
        )
        # ssh to the aster machine, run the above command
        sessions[machine_id] = subprocess.Popen(
                ['ssh', '-T', f'sjl79@aster{machine_id}.cs.pitt.edu', command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        id += 1

    # for machine_id, session in sessions.items():
    #     print(f"\n--- ASTER {machine_id} CONFIGURATION ---")
    #     for line in session.stdout:
    #         print(line, end="", flush=True)

    return sessions

def generate_machine_list(num_replicas, skipped_machines):
    # Starting at machine 20, iterate backward and add each machine that is not in skipped_machines
    # until all num_replicas have been added to the global list aster_machines_used
    global aster_machines_used

    for i in range(20,0,-1):
        if i not in skipped_machines:
            aster_machines_used.append(i)
            if len(aster_machines_used)==num_replicas:return
    # Too many skipped machines
    if len(aster_machines_used)<num_replicas:
        raise ValueError("Not enough machines available. Exiting.")


def run(args_dict:dict):

    # List of aster machine IDs to skip
    skip=[3]

    # Output configuration to console
    print("\n" + "═" * 46)
    print("           ASTER LOCAL CONTROLLER")
    print("═" * 46)
    print("═" * 46 + "\n")

    # Generate Machine list 
    generate_machine_list(args_dict['num_replicas'], skip)

    print(f"[ASTER MACHINES USED]: {', '.join(sorted(aster_machines_used))}")

    exit(0)
    
    # kill any old prime/spines/aster_replica.py processes on all aster machines
    # included in aster_machines_used
    kill_all()
    exit(0)

    # Connect to the aster machines, <clone|update> cs2910 repo, launch startup script
    sessions = start_replicas()

    for machine, process in sessions.items():
        output, _ = process.communicate()
        print(f"\n--- ASTER {machine} CONFIGURATION ---")
        print(output, flush=True)
        status = process.returncode


        for line in output.splitlines():
            if line.startswith(('#define MAX_PO_IN_FLIGHT', 'IT_LinkCrypto', 'IT_LinkEncrypt')):
                print(f'Aster {machine}: {line}', flush=True)

        if status != 0:
            print(f"Aster {machine}: FAILED (SSH exit code {status})", flush=True)
            print(output if output.strip() else "No output received from SSH.", flush=True)

    print("\n========== FINAL REPLICA STATUS ==========")
    for machine, process in sessions.items():
        print(f"Aster {machine}: {'SUCCESS' if process.returncode == 0 else 'FAILED'}")
