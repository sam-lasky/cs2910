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

import os
from pathlib import Path
from common.env_vars import get_env

# **********************************************************************
# ************************ SPINES CONFIG FILES *************************
# **********************************************************************

# Update prime/bin/spines_address.config
def spines_address_config(replica_ip_mapping):
    # writes <replica id> <replica ip>
    with open('../prime/bin/spines_address.config','w') as f:
        for key, value in replica_ip_mapping.items():
            f.write(f"{key} {value}\n")

# Update prime/spines/daemon/spines.conf
def spines_conf(replica_ip_mapping:dict,encrypted):
    new_file=''
    with open('../prime/spines/daemon/spines_template.conf', 'r') as f:
        for line in f.readlines():
            # ENCRYPTION SETTING 1
            if line.startswith('IT_LinkCrypto'):
                if encrypted:
                    line='IT_LinkCrypto = True\n'
                else:
                    line='IT_LinkCrypto = False\n'
            # ENCRYPTION SETTING 2
            elif line.startswith('IT_LinkEncrypt'):
                if encrypted:
                    line = 'IT_LinkEncrypt = True\n'
                else:
                    line = 'IT_LinkEncrypt = False\n'
            # Hosts{}    
            elif line.startswith('# List of hosts in the network'):
                hosts = 'Hosts{\n' + ''.join(f'{k} {v}\n' for k, v in replica_ip_mapping.items()) + '}\n'
                line = line + hosts
            # Edges{}
            elif line.startswith('# Each line is in form:'):
                edges = 'Edges{\n'
                sorted_keys = sorted(replica_ip_mapping.keys())
                for i in range(len(sorted_keys)):
                    for j in range(i+1, len(sorted_keys)):
                        edges+=f'{sorted_keys[i]} {sorted_keys[j]} {1}\n'
                edges +='}\n'
                line += edges
            # add line to new file
            new_file+=line

    # Write the updated file to spines.conf
    with open('../prime/spines/daemon/spines.conf', 'w') as f:
        f.write(new_file)


# **********************************************************************
# ************************ PRIME CONFIG FILES **************************
# **********************************************************************

# Update prime/bin/address.config
def address_conf(replica_ip_mapping):
    # writes <replica id> <replica ip>
    with open('../prime/bin/address.config', 'w') as f:
        for key, value in replica_ip_mapping.items():
            f.write(f"{key} {value}\n")

# Update prime/src/def.h
def def_h(NUM_F,NUM_K, MAX_PO):
    with open('../prime/src/def.h','r+') as f:
        new_file = ''
        for line in f.readlines():
            # NUM_F
            if line.startswith('#define NUM_F'):
                line = f'#define NUM_F {NUM_F}\n'
            # NUM_K
            elif line.startswith('#define NUM_K'):
                line= f'#define NUM_K {NUM_K}\n'
            # MAX_PO     
            elif line.startswith('#define MAX_PO_IN_FLIGHT'):
                line= f'#define MAX_PO_IN_FLIGHT {MAX_PO}\n'
            # Add line to the new file 
            new_file+=line
        # UPDATE FILE
        f.seek(0)
        f.write(new_file)
        f.truncate()
