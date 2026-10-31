
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
# k,v = replica id (int), replica ip (str)
replica_id_to_replica_ip={}

# Populate dictionary replica_id_to_replica_ip[replica id]= replica ip
def build_replica_id_to_replica_ip_map():
    LAN = '53' if env == 'aster_LAN_1' else '54'
    for i,aster_id in enumerate(aster_machines_used,start=1):
        replica_id_to_replica_ip[i]=f'192.168.{LAN}.{aster_id+9}'


# Args: aster_replica.py <replica_id> <aster_machine_id> <aster_machines_used> <env> <max_po> <encrypt>
def main():
    # <--- Set up global variables --->
    global replica_id, aster_machine_id, aster_machines_used, env, max_po, encrypt
    replica_id = int(sys.argv[1])
    aster_machine_id = int(sys.argv[2])
    aster_machines_used = list(map(int, sys.argv[3].split(',')))
    env = sys.argv[4]
    max_po = int(sys.argv[5])
    encrypt = int(sys.argv[6])

    # Build the replica id <--> replica ip mapping
    build_replica_id_to_replica_ip_map()
    
    # Sets up Spines
    setup_spines(replica_id_to_replica_ip,encrypt)

    # Set up Prime
    setup_prime(replica_id_to_replica_ip,num_replicas=len(replica_id_to_replica_ip.keys()),max_po=max_po) 

    # Start Spines
    
    start_spines(replica_id_to_replica_ip, replica_id)
    
    # Start Prime
    start_prime(replica_id_to_replica_ip, replica_id)

    return

if __name__ == "__main__":
    main()
