
import subprocess
import sys

# local 
sys.path.insert(0, "..")
import threads

# Stores the aster machine id of any that should not be used
skipped_machines = [3]
# List of aster machines currently in use by the test program
# Each array element is a list in the form [aster_id:int, started:Bool]
# where started indicates if the start_replica function has been called 
# on a machine w/ this id yet 
machines_in_use = []

'''
    Starts an SSH subprocess that is connects to the aster machine
    identified by the machine_id argument passed to the function & 
    updates the passed sessions dict 
'''
def start_replicas(sessions:dict):

    # Git command sent to the machine: Clone the repo if it is not in
    # the home directory, otherwise update the repo. 
    git_command = (
        '{ if [ -d cs2910/.git ]; then '
        'git -C cs2910 pull; '
        'else git clone https://github.com/sam444555/cs2910.git; '
        'fi; } > /dev/null 2>&1 && '
    )

    # Create SSH subprocesses for all machines in machines_in_use where
    # (aster_id=...,started=False), append these to sessions_new.
    for machine in machines_in_use:

        # started = T/F 
        started = machine[1]

        # Machine not started, start it. 
        if not started:

            # Get the machine's id
            machine_id = machine[0]

            # cd into the aster directory and run the aster_replica script on the replica
            # which will run until the parent process issues a termination message.
            #   aster_replica.py takes machine_id num_replicas
            #   For simplicity aster_id == replica_id
            replica_startup_command = (
                'cd cs2910/aster && '
                f'python3 -u aster_replica.py {machine_id} {len(machines_in_use)}'
            )

            # Start a new ssh subprocess & run the git and startup commands, store
            # in the dict 
            sessions[machine_id] = subprocess.Popen(
                ['ssh','-T','-o','ConnectTimeout=5',f'sjl79@aster{machine_id}.cs.pitt.edu',
                 git_command+replica_startup_command],
                 stdin=subprocess.PIPE,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 text=True
            )

            # Create a thread that monitors the SSH subprocess associated with aster # machine id 
            # Wait for the machine to respond with a 'READY' to indicate the connection was successful 
            # Otherwise TIMEOUT/FAILURE (returns T/F, respectively)
            machine[1] = threads.create_thread(target_fn='read_ssh_output',ssh_process=sessions[machine_id],timeout=3,response=[])

    
'''
    Starting at aster machine w/ id 20, iterate backwards and add each machine that is not in skipped_machines +
    machines_in_use to machines_in_use until num_replicas number of machines have been assigned. 

    If there are not enough available machines to fufill num_replicas, raise a runtime error  
'''
def generate_machine_list(num_replicas:int):

    # Total list of skips (in use & skipped)
    total_skip_list = skipped_machines + machines_in_use

    # Starting at machine 20, iterate backwards
    for aster_id in range(20,0,-1):
        # curr aster id not in the skip list, add it
        if aster_id not in total_skip_list:
            # add aster_id to in use list 
            machines_in_use.append([aster_id,False])
            # list has been filled, sort the global machines_pending and return
            if len(machines_in_use)==num_replicas:
                # sort in ascending order
                machines_in_use.sort()
                return
            
    # Not enough machines are available to fufill num_replicas 
    if len(machines_in_use)<num_replicas:
        raise ValueError("Not enough machines available. Exiting.")



    # git_command = (
    #     '{ if [ -d cs2910/.git ]; then '
    #     'git -C cs2910 pull; '
    #     'else git clone https://github.com/sam444555/cs2910.git; '
    #     'fi; } > /dev/null 2>&1 && '
    # )
    # for aster_machine_id in aster_machines_used:

    #     # CD into aster dir and startup the replica startup script
    #     replica_startup_command = (
    #         'cd cs2910/aster && '
    #         f'python3 -u aster_replica.py {id} {aster_machine_id} {args_str}'
    #     )
    #     # ssh to the aster machine, run the above command
    #     sessions[aster_machine_id] = subprocess.Popen(
    #         ['ssh', '-T', f'sjl79@aster{aster_machine_id}.cs.pitt.edu',
    #         git_command + replica_startup_command],
    #         stdin=subprocess.PIPE, #dont think we need this, used by removed functionality 
    #         stdout=subprocess.PIPE, 
    #         text=True,
    #         bufsize=1
    #     )
    #     id += 1

    # return sessions
