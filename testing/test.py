
import sys, subprocess, time, os
import csv
from pathlib import Path
from datetime import datetime

# aster_config = {
#     num_replicas: {
#         machine_id: (replica_id, ip_address)
#     }
# }
aster_config = {
    6: {
        15: (1, "192.168.53.24"),
        16: (2, "192.168.53.25"),
        17: (3, "192.168.53.26"),
        18: (4, "192.168.53.27"),
        19: (5, "192.168.53.28"),
        20: (6, "192.168.53.29"),
    },
    7: {
        14: (1, "192.168.53.23"),
        15: (2, "192.168.53.24"),
        16: (3, "192.168.53.25"),
        17: (4, "192.168.53.26"),
        18: (5, "192.168.53.27"),
        19: (6, "192.168.53.28"),
        20: (7, "192.168.53.29"),
    },
    8: {
        13: (1, "192.168.53.22"),
        14: (2, "192.168.53.23"),
        15: (3, "192.168.53.24"),
        16: (4, "192.168.53.25"),
        17: (5, "192.168.53.26"),
        18: (6, "192.168.53.27"),
        19: (7, "192.168.53.28"),
        20: (8, "192.168.53.29"),
    },
    9: {
        12: (1, "192.168.53.21"),
        13: (2, "192.168.53.22"),
        14: (3, "192.168.53.23"),
        15: (4, "192.168.53.24"),
        16: (5, "192.168.53.25"),
        17: (6, "192.168.53.26"),
        18: (7, "192.168.53.27"),
        19: (8, "192.168.53.28"),
        20: (9, "192.168.53.29"),
    },
    10: {
        11: (1, "192.168.53.20"),
        12: (2, "192.168.53.21"),
        13: (3, "192.168.53.22"),
        14: (4, "192.168.53.23"),
        15: (5, "192.168.53.24"),
        16: (6, "192.168.53.25"),
        17: (7, "192.168.53.26"),
        18: (8, "192.168.53.27"),
        19: (9, "192.168.53.28"),
        20: (10, "192.168.53.29"),
    },
}


def main():
    # Total number of trials each test configuration runs 
    num_trials = 5
    # MAX_PO_IN_FLIGHT values tested (prime/src/def.h)
    max_po_list = [20, 100, 500, 1000, 2500, 5000, 10000, 25000]
    # Number of Replicas tested (NUM_SERVERS=(3*NUM_F + 2*NUM_K + 1) in prime/src/def.h)
    total_replicas_used = [6,7,8,9,10]
    # Number of emulated clients (prime/src/driver.c)
    emulated_list = [20, 100, 500, 1000, 2500, 5000, 10000, 25000]
    # Encrypted Status (0=False,1=True)
    encrypted = [0]
    
    # Total updates sent per individual test
    updates=25000
     

    filename = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    # Test diff num of replicas [6 thru 10]
    for num_replicas in total_replicas_used:
        # Test encrypted [0=True,1=False]
        for encrypted in [0]:
            # Test different MAX_PO values
            for max_po in max_po_list:
                # Distribution (Number of replicas running drivers, each assigned an equal share of total updates)
                 for distribution in range(1,num_replicas+1):
                    # Execute run which runs num_replicas aster machines where each machine
                    # is using the current encryption status and max_po value 
                    subprocess.run([
                        sys.executable, "run.py",
                        "-e", "aster_LAN_1",
                        "-x", str(encrypted),
                        "-p", str(max_po),
                        "-r", str(num_replicas) ]
                        , check=True)
                    # Test out different emulated client values in driver.c
                    for emulated_client in emulated_list:
                        # Conduct num_trials of the current config
                        for trial in range(1,num_trials+1):
                            # Get the machines used
                            machines = aster_config[distribution]
                            # Get the updates per machine
                            updates_distributed = updates//distribution
                            # Start a driver program on all machines being used
                            for machine_id, (replica_id, ip) in aster_config[distribution].items():
                                print(machine_id, replica_id, ip)
                                exit(0)


if __name__ == '__main__':
    main()
