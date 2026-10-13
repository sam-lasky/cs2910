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

import sys, subprocess, os, ipaddress; from pathlib import Path

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
def load_replica_configuration(config):
    # path to the file containing the replica ip addresses
    flie_path = None
    
    # Choice 1: aster 
    if config =='aster': file_path =  'config_files/aster_machines_used.txt'
    # Choice 2: docker
    elif config=='docker':file_path= 'config_files/docker_containers_used.txt'
    # Choice 3: existing - replica ip addresses already located in replica_ip_addresses.txt
    elif config=='existing':file_path= 'config_files/replica_ip_addresses.txt'
    # Invalid Choice: raise error
    else: raise ValueError(f'Invalid Selection: {config}')

    # Open the file, confirm IP addresses are valid & write to 
    # replica_ip_addresses.txt if environment=aster|docker. If environment=existing,
    # check if the current configuration is valid. 

    # Tracks number of replicas - this value serves as the unique replica 
    # identifier (must be a positive int from 1->N) and is assigned its ID by 
    # line number (replica with ip on line i gets ID i, replica with ip on line i+1 gets ID i+1, etc)
    num_of_replicas = 0

    # List of tuples holding the candidate replicas where each entry is (<replica_id>,<replica_ip>)
    candidate_replicas=[]
    try:
        with open(file_path,'r') as f:
            for line in f:
                # get line as a list, separated by whitespace 
                line= line.split()
                # skip comments and empty lines
                if line[0]=='#' or len(line)==0:continue
                # checks if line is a valid ip address, if not raises an exception
                ipaddress.IPv4Address(line[0])
                # valid line, increment number of replicas 
                num_of_replicas+=1
                # Replica id assignment - final line format in: <replica_id> <replica_ip>
                candidate_replicas.append((num_of_replicas,line[0]))

    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    # validate the candidate_replicas list & return it. 
    validate_config(candidate_replicas)
    return candidate_replicas

# updates the following config files with the using the 
# validated replicas:
# 1. prime/bin/address.config
# 2. prime/bin/spines_address.config
# 3. prime/spines/daemon/spines.conf
def update_files(replica_list,config):
    # write to prime/bin/address.config then prime/bin/spines_address.config
    # both share the same line structure <replica_id> <replica_ip>
    for config_path in ['../prime/bin/address.config', '../prime/bin/spines_address.config']:
        with open(config_path, "w") as f:
            for replica in replica_list:
                replica_id = replica[0]
                replica_ip = replica[1]
                # write line in form <replica_id> <replica_ip>
                f.write(f'{replica_id} {replica_ip}')

    # create spines.conf by appending the replica configuration 
    # information to examples_spines.conf 
    example_spines_lines = None
    with open('../prime/spines/daemon/example_spines.conf','r') as f:
        example_spines_lines=f.readlines()
    # create & write or overwrite '../prime/spines/daemon/example_spines.conf'
    with open('../prime/spines/daemon/spines.conf','w') as f:
        for line in example_spines_lines:
            check_line = line.split()
            # check if we are at the line where to start writing the replica information
            # or edge information
            if check_line and check_line[0] in ['Hosts{','Edges{']:
                # we are, write the current line and then write all the replica info 
                f.write(line)
                hosts=[]
                # writing Hosts{...}
                if check_line[0]=='Hosts{':      
                    for replica in replica_list:
                        replica_id = replica[0]
                        replica_ip = replica[1]
                        # write <replica_id> <replica_ip> in Hosts{...}
                        hosts.append(f'\t{replica_id} {replica_ip}')
                    f.write('\n'.join(hosts))
                # writing Edges{...}
                else:
                    edges=[]
                    for i in range(0,len(replica_list)):
                        for j in range(i+1,len(replica_list)):
                            # write edge <replica_id replica_list[i]> <replica_id replica_list[j]> <cost>
                            edges.append(f'\t{replica_list[i][0]} {replica_list[j][0]} 1')
                    f.write('\n'.join(edges))
            # we're not, write whatever is in the current line 
            else:
                f.write(line)

# <docker>: builds the configuration using the container ip addresses located in config_files/docker_containers_used.txt
# <aster>: builds the configuration using the aster machine ip addresses located in config_files/aster_machines_used.txt
# <skip>: this entire process is skipped & assumes the configuration information is correct.   
def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['docker', 'aster','existing_fresh','existing_preserve','skip']:
        print("Usage: python config.py <docker|aster|skip>")
        sys.exit(1)
    
    # get the config type 
    config = sys.argv[1]
    
    # check if we are skipping the configuration process
    if config=='skip':
        print("Skipping the configuration process")
        return
 
    # load the replica config from the text files
    replica_list = load_replica_configuration(config)
   
    # update prime/spines configuration files
    update_files(replica_list, config)

if __name__=="__main__":
    main()