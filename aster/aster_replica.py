
import sys
import subprocess
import time
import os
# local 
sys.path.insert(0, "..")
from common.spines_manager import *
from common.prime_manager import *

# Globals
replica_id = None
machine_id = None
aster_machines_used = []
env = None
max_po = None
encrypt = None
# k,v = replica id (int), replica ip (str)
replica_ip={}

# fills in replica_ip dict where replica_ip[replica id]= replica ip
def build_replica_ip_map():
    LAN = '53' if env == 'aster_LAN_1' else '54'
    for i,aster_id in enumerate(aster_machines_used,start=1):
        replica_ip[i]=f'192.168.{LAN}.{aster_id+9}'


# Args: aster_replica.py <replica_id> <machine_id> <aster_machines_used> <env> <max_po> <encrypt>
def main():
    # <--- Set up global variables --->
    global replica_id, machine_id, aster_machines_used, env, max_po, encrypt
    replica_id = int(sys.argv[1])
    machine_id = int(sys.argv[2])
    aster_machines_used = list(map(int, sys.argv[3].split(',')))
    env = sys.argv[4]
    max_po = int(sys.argv[5])
    encrypt = int(sys.argv[6])

    # # Print config for controller
    # print(f"\n{'ASTER':<8} {'REPLICA':<10} {'ENVIRONMENT':<14} {'MAX_PO':<10} {'ENCRYPTED':<12}")
    # print("-" * 54)
    # for rid, mid in enumerate(aster_machines_used, start=1):
    #     print(f"{mid:<8} {rid:<10} {env:<14} {max_po:<10} {encrypt:<12}")

    # Build the replica id <--> replica ip mapping
    build_replica_ip_map()
    
    # Sets up Spines
    setup_spines(replica_ip,encrypt)
    # Set up Prime
    setup_prime(replica_ip,num_replicas=len(replica_ip.keys()),max_po=max_po) 

    # Start Spines
    start_spines(replica_ip, replica_id)
    # Start Prime
    start_prime(replica_ip, replica_id)

    return

if __name__ == "__main__":
    main()
