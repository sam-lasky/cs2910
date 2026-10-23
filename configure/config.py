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


# Modifies MAX_PO_IN_FLIGHT and NUM_K/NUM_F based on env var MAX_PO and NUM_REPLICAS respectively
def update_def_h():

    configurations = {
        6: (1, 1),
        8: (1, 2),
        10: (1, 3),
        12: (1, 4),
        14: (3, 2),
        16: (5, 0),
        18: (5, 1),
        20: (5, 2)
    }

    f, k = configurations[get_env('NUM_REPLICAS')]
    MAX_PO_IN_FLIGHT= get_env('MAX_PO')

    # new def_h
    new_def = ''

    with open('../prime/src/def.h','r') as f:
        for line in f.readlines():
            # update max po in flight
            if line.startswith('#define MAX_PO_IN_FLIGHT'):
                line=f'#define MAX_PO_IN_FLIGHT {MAX_PO_IN_FLIGHT}\n'
            # update num_f
            if line.startswith('#define NUM_F ='):
                line=f'NUM_F = {f}\n'
            if line.startswith('NUM_K ='):
                line=f'#define NUM_K = {k}\n'
            new_def+=line

    # update def.h w/ new f,k vals
    with open('../prime/src/def.h', 'w') as file:
        file.write(new_def)


# All configuration information is stored as environment 
# variables & will be retrieved as needed.  
def main():
    # load the replica config 
    replica_list = load_replica_configuration()

    # update config files
    update_files(replica_list,os.environ['ENCRYPTED'])

    # update def.h using the passed MAX_PO_IN_FLIGHT,NUM_F,NUM_K vals
    update_def_h()



if __name__=="__main__":
    main()