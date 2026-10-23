import sys, subprocess, time, os, socket, platform
from common.env_vars import store_env, get_env

# Final selection of machines that will be used after
# looking at both aster_machines_used.txt and barred_machines.txt
final_list = []

# Kills any leftover prime, spines or aster_replica processes contained in 
# the machine list
def kill_all():
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
    # unique id of the replica
    id=1
    for machine in final_list:
        print(f'Starting session with Aster {machine}')

        subprocess.Popen(
            f'ssh sjl79@aster{machine}.cs.pitt.edu '
            f'"output=$(git -C cs2910 pull 2>&1 || git clone https://github.com/sam444555/cs2910.git 2>&1); '
            f'cd cs2910/aster && '
            f'python3 -u aster_replica.py {id} {machine} \\"$output\\""'
        )
        id += 1

def run():
    print('[Aster Controller Local]')
    
    # finalize list of aster machines that will be used
    select_replica_machines()
    print(f'Using machines:{','.join(final_list)}')
    
    # kill any old prime/spines/aster_replica.py processes on these machines
    kill_all()

    # Connect to the aster machines, <clone|update> cs2910 repo, launch startup script
    start_replicas()

    exit(0)


#     # Start new sessions
#     sessions = {}
#     id =1
#     for i in range(13, 19):
#         print(f'Starting session with Aster {i}')
#         sessions[i] = subprocess.Popen(
#             f'ssh sjl79@aster{i}.cs.pitt.edu '
#             f'"output=$(git -C cs2910 pull 2>&1 || git clone https://github.com/sam444555/cs2910.git 2>&1); '
#             f'echo \\"$output\\"; '
#             f'cd cs2910/aster && '
#             f'python3 -u startup_replica.py {id} {max_po} {encrypted} \\"$output\\""',
#             creationflags=subprocess.CREATE_NEW_CONSOLE
#         )
#         id+=1

#     # wait for replicas to initialize
#     print("Waiting 60 seconds for replicas to initialize...", flush=True)
#     time.sleep(60)
#     # run tests
#     run_tests(sessions, max_po, encrypted)
#     # wait 10 secs 
#     print("Waiting 10 seconds before cleanup...", flush=True)
#     time.sleep(10)
#     # terminate all sessions 
#     kill_all(sessions)


# if __name__=='__main__':
#     main()
