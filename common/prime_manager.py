import subprocess
import os
import sys
import time
# local imports
from common.config import address_conf, def_h

# Maps the total number of replicas (int) to (NUM_F, NUM_K).
configurations = {
    6: (1, 1),
    7: (1, 2),
    8: (1, 2),
    9: (2, 1),
    10: (1, 3),
    11: (2, 2),
    12: (1, 4),
    13: (2, 3),
    14: (3, 2),
    15: (2, 4),
    16: (1, 6),
    17: (2, 5),
    18: (1, 7),
    19: (2, 6),
    20: (1, 8),
    21: (2, 7),
    22: (1, 9),
    23: (2, 8),
    24: (1, 10),
    25: (2, 9),
    26: (1, 11),
    27: (2, 10),
    28: (1, 12),
    29: (2, 11),
    30: (1, 13),
}

# Set up Prime
def setup_prime(replica_ip:dict, num_replicas:int, max_po:int):
    # Update prime/bin/address.config
    address_conf(replica_ip)
   
    # Update prime/src/def.h
    num_replicas = num_replicas
    max_po = max_po
    num_f, num_k = configurations[num_replicas]
    def_h(NUM_F=num_f, NUM_K=num_k, MAX_PO=max_po)
    
    # Path to Prime
    prime_path = "../prime"

    # Build Prime
    build_prime(prime_path)

    # Copy Prime keys for this replica count.
    subprocess.run(
        [
            "cp", "-a",
            f"../keys/saved_keys/prime_keys/replicas_{num_replicas}/keys/.",
            prime_path + "/bin/keys/",
        ],
        check=True,
    )


# Builds Prime:
# 1. Sets execute permissions on dependency configure scripts and build tools.
# 2. Runs make clean in prime/src to remove previous build outputs.
# 3. Runs make -j1 to build Prime using one job at a time.
def build_prime(prime_path):
    try:
        subprocess.run(
            "chmod +x stdutil/configure && "
            "chmod -R +x stdutil/buildtools && "
            "chmod +x libspread-util/configure && "
            "chmod -R +x libspread-util/buildtools && "
            "chmod +x OpenTC-1.1/TC-lib-1.0/configure && "
            "chmod +x OpenTC-1.1/TC-lib-1.0/missing",
            cwd=prime_path,
            shell=True,
            check=True
        )

        subprocess.run(
            ["make", "clean"],
            cwd=prime_path + "/src",
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["make", "-j1"],
            cwd=prime_path + "/src",
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        print(f"ERROR: Prime setup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)


# Start Prime
def start_prime(replica_ip:dict, replica_id:int):

    with open('status.log', 'w') as prime_status_log:
        # Start the Prime Process, write stdout/err to prime_status_log
        prime = subprocess.Popen(
            ["./prime", "-i", str(replica_id), "-g", str(replica_id)],
            cwd='../prime/bin',
            stdout=prime_status_log,
            stderr=prime_status_log
        )

    # Loop until all handshakes are completed
    while True:
        time.sleep(1)
        # Checkup on Spines
        #   poll() return values:
        #       None: Process still executing
        #       0: Process successfully exited
        #       Nonzero int: Process exited w/ error
        if prime.poll() is not None:
            raise RuntimeError(f'Prime exited during startup')
        else:
            # Check log file for handshake msgs
            with open('status.log', 'r') as prime_status_log:
                for line in prime_status_log.readlines():
                    if line.startswith('Called PR_Resume_Normal_operations'):
                        time.sleep(2)
                        return prime