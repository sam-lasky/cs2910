import sys, subprocess, time, os, socket, platform
from common.env_vars import store_env, get_env

# IDs of machines being used ([1,2,3] = aster1/2/3 being used)
aster_machines_used = []

# Kills any leftover prime, spines or aster_replica processes contained in 
# the machine list
def kill_all():
    print('\n[KILLING EXISTING PROCESSES]')
    for m in aster_machines_used:
        print(f"Cleaning Aster{m}...", flush=True)
        subprocess.run(
            [
                "ssh",
                f"sjl79@aster{m}.cs.pitt.edu",
                "pkill -x prime; pkill -x spines; pkill -f '[a]ster_replica.py'"
            ],
            check=False
        )


def connection_test():
    print('\n[TESTING CONNECTIONS TO ALL MACHINES]')
    for machine in sorted(aster_machines_used):
        p=subprocess.run(['ssh',f'sjl79@aster{machine}.cs.pitt.edu'],capture_output=True,text=True)
        message = f"ASTER_{machine} CONNECTION STATUS: {'SUCCESS' if p.returncode == 0 else 'FAILED'}"
        if p.returncode!=0:
            message+=f'\nERROR MESSAGE:{p.stderr}'
            if 'Connection timed out' in p.stderr:
                message+='Are you connected to GlobalProtect?'
            print(message)
            exit(1)
        print(message)
        

def run(args_dict:dict):

    # List of aster machine IDs to skip
    skip=[3]

    # Output configuration to console
    print("\n" + "═" * 46)
    print("           ASTER LOCAL CONTROLLER")
    print("═" * 46 + "\n")

    # Generate Machine list 
    generate_machine_list(args_dict['num_replicas'], skip)

    # Prints all machines & ips being used 
    print_machines(env=args_dict['env'])

    # Attempt to connect to all the machines being used. Terminates if all connections do not succeed
    connection_test()

    # Kill any old prime/spines/aster_replica.py processes on all aster machines
    # included in aster_machines_used
    kill_all()

    # Connect to the aster machines, <clone|update> cs2910 repo, launch startup script
    sessions = start_replicas(args_dict)

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

# For all aster machines in aster_machines_used:
#   (1) Connect to the machine
#   (2) Clone or update cs2910 repo
#   (3) Launch aster_replica.py
def start_replicas(args_dict):
    # Convert aster_machines_used from list to comma separated string to be passed to aster_replica.py
    aster_machines_used_as_str = ','.join(map(str, aster_machines_used))
    # Get the environment
    env = args_dict['env']
    # Get the max_po
    max_po = args_dict['max_po']
    # Get encrypted (0/1)
    encrypt = args_dict['encrypt']
    # Generate the argument list: 
    args_str = f"{aster_machines_used_as_str} {env} {max_po} {encrypt}" 
   
    # ssh sessions, session[i] = subprocess of aster machine i (where 1<=i<=20)
    sessions = {}
    # unique id of the replica
    id=1
    print('\n[STARTING MACHINES]')
    for aster_machine_id in aster_machines_used:
        print(f'Starting session with Aster {aster_machine_id}')

        # Updates the repo if it exists, otherwise clones it. 
        # Purges stdout/err by writing to dev/null
        git_command = (
            'if [ -d cs2910/.git ]; then '
            f'git -C cs2910 pull; '
            f'else git clone https://github.com/sam444555/cs2910.git; '
            'fi && '
        )

        # CD into aster dir and startup the replica startup script
        replica_startup_command = (
            'cd cs2910/aster && '
            f'python3 -u aster_replica.py {id} {aster_machine_id} {args_str}'
        )

        # ssh to the aster machine, run the above command
        sessions[aster_machine_id] = subprocess.Popen(
                ['ssh', '-T', f'sjl79@aster{aster_machine_id}.cs.pitt.edu', git_command+replica_startup_command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        id += 1

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

def print_machines(env:str):
        machines = sorted(aster_machines_used)
        print(f"[ASTER MACHINES USED]")
        for aster_id in machines:
            LAN_TYPE = 'LAN_1' if env=='aster_1_LAN' else 'LAN_2'
            LAN_IP_VAL = '53' if env=='aster_1_LAN' else '54'
            IP = f'192.168.{LAN_IP_VAL}.{aster_id+9}'
            print(f'ASTER_{aster_id}\tLAN:{LAN_TYPE}\tIP:{IP}')