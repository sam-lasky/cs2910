
import sys
import subprocess
import time
import os
# local 
sys.path.insert(0, "..")
from common.spines_manager import *
from common.prime_manager import *

# * * * ** * * ** * * * *
# * * * * GLOBALS * * * *
# * * * ** * * ** * * * *

# Unique integer identifier of the Replica 
replica_id = None
# Unique integer identifer of the Aster Machine
aster_machine_id = None
# List of all machines being used
aster_machines_used = []
# Environment being used <Docker | Aster_1_LAN | Aster_2_LAN>
env = None
# MAX_PO_IN_FLIGHT (prime/src/def.h)
max_po = None
# Encrypted or Plain (prime/spines/daemon/spines.conf, IT_LinkCrypto, IT_LinkEncrypt)
encrypt = None
# k,v = REPLICA id (int), replica ip (str)
id_to_ip={}

# Populates the id_to_ip dictionary where the >> REPLICA ID<< is passed as the
# key and its IP is assigned as the value 
def build_id_to_ip_map():
    # 53 if LAN_1, 54 if LAN_2
    LAN = '53' if env == 'aster_LAN_1' else '54'
    for i,aster_id in enumerate(aster_machines_used,start=1):
        id_to_ip[i]=f'192.168.{LAN}.{aster_id+9}'


# Args: aster_replica.py <arg_replica_id> <arg_aster_machine_id> <arg_aster_machines_used> <arg_env> <arg_max_po> <arg_encrypt>
def main(arg_replica_id, arg_aster_machine_id, arg_aster_machines_used, arg_env, arg_max_po, arg_encrypt):
    # <--- Set up global variables --->
    global replica_id, aster_machine_id, aster_machines_used, env, max_po, encrypt
    # Integer (>0) that uniquely identifies the replica
    replica_id =                int(sys.argv[1])
    # Integer (1-->20) that uniquely identifies the aster machine
    aster_machine_id =          int(sys.argv[2])
    # List of aster ID's being used
    aster_machines_used =       list(map(int, sys.argv[3].split(',')))
    # Environment (aster LAN 1 | aster LAN 2)
    env =                       sys.argv[4]
    # Max preorder requests in flight (prime/src/def.h)
    max_po =                    int(sys.argv[5])
    # Spines encryption (enabled=1, disabled=0)
    encrypt =                   int(sys.argv[6])

    # Build the aster machine id <--> replica ip mapping
    build_id_to_ip_map()
    
    # Sets up Spines
    setup_spines(id_to_ip,encrypt)

    # Set up Prime
    setup_prime(id_to_ip,num_replicas=len(id_to_ip.keys()),max_po=max_po) 

    # Start Spines
    
    start_spines(id_to_ip, replica_id)
    
    # Start Prime
    start_prime(id_to_ip, replica_id)

    return

if __name__ == "__main__":
    main()
