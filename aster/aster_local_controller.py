import sys, subprocess, time, os, socket, platform
from common.env_vars import store_env, get_env

# Final selection of machines that will be used after
# looking at both aster_machines_used.txt and barred_machines.txt
final_list = []

# Kills any leftover prime, spines or aster_replica processes contained in 
# the machine list
def kill_all():
    print('\n[KILLING EXISTING PROCESSES]')
    for m in final_list:
        print(f"Cleaning Aster{m}...", flush=True)
        subprocess.run(
            [
                "ssh",
                f"sjl79@aster{m}.cs.pitt.edu",
                "pkill -x prime; pkill -x spines; pkill -f '[a]ster_replica.py'"
            ],
            check=False
        )

# Get all the aster machines indicated by the contents of aster_machines_used.txt
# and barred_machines.txt
def select_replica_machines():
    global final_list

    # Get list of machines not to not use
    barred_machines = get_machines('aster/barred_machines.txt')
    # Get list of selected machines
    selected_machines = get_machines('aster/aster_machines_used.txt')
    # Remove barred machines and sort
    final_list = sorted(set(selected_machines) - set(barred_machines), key=int)
    # Keep only the number of machines needed
    del final_list[get_env('NUM_REPLICAS'):]

    # Check for mismatch between total num of selected machines and num replicas being used
    if len(final_list)!= get_env('NUM_REPLICAS'):
       error_handler(f"Expected {os.environ['NUM_REPLICAS']} total machines, but found {len(final_list)}.")
    # Match, create and set ASTER_MACHINES_USED environment var to final_list
    else:
        store_env('ASTER_MACHINES_USED', ','.join(final_list))


# Gets all the selected aster machines indicated by the file, where
# file = <aster_machines_used | barred_machines>. Returns a list. 
def get_machines(file_path):
    with open(file_path, 'r') as f:
        machine_list = []
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.isdecimal() and 1 <= int(line) <= 20:
                machine_list.append(line)
            else:
                error_handler(f'Invalid machine ID: {line}. Expected a value in range 1->20')
    return machine_list

# Prints out any errors encountered, terminates the program. 
def error_handler(err_msg:str):
    print(['ERROR'])
    print(err_msg)
    exit(1)


# For all aster machines in final_list:
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
    for machine_id in final_list:
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

def run(args_dict:dict,keygen:bool=False):
    # Special Case: keygen

    # Output configuration to console
    print("\n" + "═" * 46)
    print("           ASTER LOCAL CONTROLLER")
    print("═" * 46)
    print("═" * 46 + "\n")

    # finalize list of aster machines that will be used
    select_replica_machines()
    print(f'[ASTER MACHINES USED]:{','.join(final_list)}')
    
    # kill any old prime/spines/aster_replica.py processes on all aster machines
    # included in final_list
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
