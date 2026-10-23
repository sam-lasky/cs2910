import sys, subprocess, time, os, socket, platform
from common.env_vars import store_env

# Final selection of machines that will be used after
# looking at both aster_machines_used.txt and barred_machines.txt
final_list = []

# Kills any leftover prime, spines or aster_replica processes contained in 
# the machine list
def kill_all(machines):
    for m in machines:
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
    barred_machines = get_machines('barred_machines.txt')
    # Get list of selected machines
    selected_machines = get_machines('aster_machines_used.txt')
    # Get final list
    final_list = sorted([m for m in selected_machines if m not in barred_machines], key=int)    

    # Check for mismatch between total num of selected machines and num replicas being used
    if len(final_list)!=os.environ['NUM_REPLICAS']:
        error_handler(f'Expected {os.environ['NUM_REPLICAS']} total machines, but found {len(final_list)}.')
    # Match, create and set ASTER_MACHINES_USED environment var to final_list
    else:
        store_env('ASTER_MACHINES_USED', ','.join(final_list))

# Gets all the selected aster machines indicated by the file, where
# file = <aster_machines_used | barred_machines>. Returns a list. 
def get_machines(file_path):
    with open(file_path,'r') as f:
        machine_list=[]
        for line in f.readlines():
            line.strip()
            if line and not line.startswith('#'):
                if line.isdecimal() and int(line)>0 and int(line)<21:
                    machine_list.append(line)
            else:
                error_handler(f'Invalid machine ID: {line}. Expected a value in range 1->20')
    return machine_list

# Prints out any errors encountered, terminates the program. 
def error_handler(err_msg:str):
    print(['ERROR'])
    print(err_msg)
    exit(1)


def run():
    print('[Aster Controller Local]')
    select_replica_machines()
    print(f'Using machines:{final_list}')





#     import sys, subprocess, time, os, socket, platform

# def kill_all(sessions):
#     if sessions is None:
#         for i in range(13, 19):
#             print(f"Cleaning Aster{i}...", flush=True)
#             subprocess.run(
#                 [
#                     "ssh",
#                     f"sjl79@aster{i}.cs.pitt.edu",
#                     "pkill -x prime; pkill -x spines"
#                 ],
#                 check=False
#             )        
#         return
#     for i, process in sessions.items():
#         # Kill Prime, Spines, and startup script on remote machine
#         subprocess.run(
#             [
#                 "ssh",
#                 f"sjl79@aster{i}.cs.pitt.edu",
#                 "pkill -x prime; pkill -x spines; pkill -f '[s]tartup_replica.py'"
#             ],
#             check=False
#         )

#         # Close local terminal window
#         subprocess.run(
#             ["taskkill", "/F", "/T", "/PID", str(process.pid)],
#             stdout=subprocess.DEVNULL,
#             stderr=subprocess.DEVNULL
#         )
#     # closes terminal windows
#     sessions.clear()


# def run():
#     print('[Aster Controller Local]')
#     exit()


# def main():
#     # Kill any existing replica startup scripts
#     print("Terminating any existing Prime and Spines processes on Aster machines...", flush=True)    
#     kill_all(None)

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
