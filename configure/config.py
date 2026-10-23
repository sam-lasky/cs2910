# ============================================================
# CS2910 — Master's Project
# University of Pittsburgh
#
# Author: Samuel Lasky
# Project: Prime — Byzantine Fault-Tolerant Replication
#
# Developed in fulfillment of the Master's Project
# requirement for the M.S. in Computer Science.
# ============================================================

import sys, subprocess, os, ipaddress, json; from pathlib import Path
import time
from common.env_vars import get_env

# Inputs the list of candidate replicas (replica_list) which consists
# of the replicas being used where each entry is a tuple in the form 
# (replica_ip_address, replica_id)
# Checks the list to see if it satisfies the required number of  servers as 
# defined in prime/src/def.h NUM_SERVERS=(3*NUM_F + 2*NUM_K + 1) where 
# NUM_F is the maximum number of tolerated byzantine faults and NUM_K is
# the maximum number of benign faults. An error is reported & the program is exited
#  if this requirement is not satisfied, otherwise it returns to the calling function. 
def validate_config(replica_list):
    # open def.h
    with open('../prime/src/def.h','r') as f:
        NUM_F = None
        NUM_K = None

        for line in f:
            # max num of tolerated byzantine faults
            if line.startswith('#define NUM_F'):
                NUM_F=line.split()[2]
            # max num of tolerated benign faults 
            elif line.startswith('#define NUM_K'):
                NUM_K=line.split()[2]
            # exit case: both values retrieved
            if (NUM_F is not None) and( NUM_K is not None):break

    try:
        # Get NUM_SERVERS (3*NUM_F + 2*NUM_K + 1)
        NUM_SERVERS = ((3* int(NUM_F)) + (2* int(NUM_K)) + 1)
        # check if the required number are not met, if so raise 
        # an error and terminate otherwise return 
        if(len(replica_list) is not NUM_SERVERS):
            raise ValueError(f"Invalid number of replicas:{NUM_SERVERS} is required, {len(replica_list)} is what was given")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def modify_fault_tolerance(num_replicas):
    configurations = {
        6: (1, 1),
        7: (2, 0),
        8: (1, 2),
        9: (2, 1),
        10: (3, 0),
        11: (2, 2),
        12: (3, 1),
        13: (4, 0),
        14: (3, 2),
        15: (4, 1),
        16: (5, 0),
        17: (4, 2),
        18: (5, 1),
        19: (6, 0),
        20: (5, 2)
    }

    f, k = configurations[num_replicas]

    path = '../prime/src/def.h'

    with open(path) as file:
        contents = file.read()

    import re
    contents = re.sub(r'(#define NUM_F\s+)\d+', lambda m: m.group(1) + str(f), contents)
    contents = re.sub(r'(#define NUM_K\s+)\d+', lambda m: m.group(1) + str(k), contents)

    with open(path, 'w') as file:
        file.write(contents)

    print(f'NUM_F = {f}, NUM_K = {k}', flush=True)


# parses the <aster_machines_used || docker_containers_used || replica_ip_addresses.txt> depending on config type 
# returns a list of tuples of all the replicas where each tuple is in the form (replica_ip, replica_id)
def load_replica_configuration():
    # List of tuples holding the candidate replicas where each entry is (<replica_id>,<replica_ip>)
    candidate_replicas=[]

    # <aster1|aster2>
    if get_env('ENVIRONMENT') in ['aster1','aster2']:
        machines = get_env('ASTER_MACHINES_USED')
        network = '53' if '1' in os.environ['ENVIRONMENT'] else '54'
        id=1
        for m in machines:
            candidate_replicas.append((id,f'192.168.{network}.{int(m)+9}'))
            id+=1
    # docker
    else:
        #TODO: COMPLETE ME
        pass

    # Lets hope commenting this out doesn't break it!
    # validate the candidate_replicas list & return it. 
    # validate_config(candidate_replicas)
    return candidate_replicas

# updates the following config files with the using the 
# validated replicas:
# 1. prime/bin/address.config
# 2. prime/bin/spines_address.config
# 3. prime/spines/daemon/spines.conf
def update_files(replica_list,encrypted):
    # records the directory of a file that has changed
    updated_directories=[]
    # Create the output to both files. It is identical for both cases.
    out=''
    for replica in replica_list:
        replica_id = replica[0]
        replica_ip = replica[1]
        # write line in form <replica_id> <replica_ip>
        out+=f'{replica_id} {replica_ip}\n'

    # first read in the file, compare it with out, and if it has changed replace it 
    # and record the directory otherwise do nothing
    for config_path in ['../prime/bin/address.config', '../prime/bin/spines_address.config']:
        with open(config_path, "r") as f:
            old_file = f.read()
        # files are not the same, update & record
        if old_file!=out:
            with open(config_path, 'w') as f:
                f.write(out)
            updated_directories.append('prime')

    # create spines.conf by appending the replica configuration 
    # information to examples_spines.conf 
    new_spines_conf=''
    with open('../prime/spines/daemon/example_spines.conf','r') as f:
        for line in f:
            # split the line
            check_line= line.split()
            # line nonempty & on the Hosts or Edges line 
            if check_line and check_line[0] in ['Hosts{','Edges{']:
                # Add the Hosts{ or Edges{ line to new_spines_conf 
                new_spines_conf+=line
                # writing Hosts{...}
                if check_line[0]=='Hosts{':
                    for replica in replica_list:
                        # Add <replica_id> <replica_ip> in Hosts{...}
                        new_spines_conf += f'\t{replica[0]} {replica[1]}\n'
                # writing Edges{...}
                else:
                    for i in range(0,len(replica_list)):
                        for j in range(i+1,len(replica_list)):
                            # write edge <replica_id replica_list[i]> <replica_id replica_list[j]> <cost>
                            new_spines_conf+= f'\t{replica_list[i][0]} {replica_list[j][0]} 1\n'
            # neither case applies, add line as is
            else:
                new_spines_conf+=line

        if encrypted=='encrypted':
            new_spines_conf = new_spines_conf.replace('IT_LinkCrypto = False', 'IT_LinkCrypto = True')
            new_spines_conf = new_spines_conf.replace('IT_LinkEncrypt = False', 'IT_LinkEncrypt = True')

    # Get the contents of the old spines.conf
    old_spines_conf = ''
    if os.path.exists('../prime/spines/daemon/spines.conf'):
        with open('../prime/spines/daemon/spines.conf','r') as f:
            old_spines_conf=f.read()

    # If files dont not match, replace spines.conf and record 
    # the directory in which this update occurred.
    if new_spines_conf!=old_spines_conf:
        with open('../prime/spines/daemon/spines.conf','w') as f:
            f.write(new_spines_conf)
            updated_directories.append('spines')

    # return all the dirs that were changed
    return updated_directories


# modifies MAX_PO_IN_FLIGHT based off the CLI argument provided 
def modify_max_po(MAX_PO_IN_FLIGHT):
    file_content = ''
    updated = 0

    with open('../prime/src/def.h','r') as f:
        for line in f.readlines():
            check_line = line.split()
            if len(check_line)==3 and check_line[1] == 'MAX_PO_IN_FLIGHT':
                # check if max_po vals are not the same & update line accordingly if it is the case
                if int(check_line[2])!=MAX_PO_IN_FLIGHT:
                    updated=1
                    line=f'#define MAX_PO_IN_FLIGHT {MAX_PO_IN_FLIGHT}\n'
            file_content+=line

    if updated:
        with open('../prime/src/def.h','w') as f:
            f.write(file_content)
    return updated

# All configuration information is stored as environment 
# variables & will be retrieved as needed.  
def main():
    # load the replica config 
    replica_list = load_replica_configuration()

    # update config files
    update_files(replica_list,os.environ['ENCRYPTED'])
    
    # modify MAX_PO_IN_FLIGHT
    modify_max_po(get_env('MAX_PO'))

    # modify num replicas
    modify_fault_tolerance(len(replica_list))



if __name__=="__main__":
    main()