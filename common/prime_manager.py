import subprocess
import os
import sys
import time
# local imports
from common.config import address_conf, def_h

# Maps:  (KEY,type=INT)Total Number of Replicas: (VAL,type=INT TUPLE)(NUM_F, NUM_K)
# such that the equation in prime/src/def.h NUM_SERVERS (3*NUM_F + 2*NUM_K + 1)
# is satisfied 
configurations = {
    # 3(1) + 2(1) + 1 = 6
    6: (1, 1),
    # 3(2) + 2(0) + 1 = 7
    7: (2, 0),
    # 3(1) + 2(2) + 1 = 8
    8: (1, 2),
    # 3(2) + 2(1) + 1 = 9
    9: (2, 1),
    # 3(1) + 2(3) + 1 = 10
    10: (1, 3),
    # 3(2) + 2(2) + 1 = 11
    11: (2, 2),
    # 3(1) + 2(4) + 1 = 12
    12: (1, 4),
    # 3(2) + 2(3) + 1 = 13
    13: (2, 3),
    # 3(3) + 2(2) + 1 = 14
    14: (3, 2),
    # 3(2) + 2(4) + 1 = 15
    15: (2, 4),
    # 3(1) + 2(6) + 1 = 16
    16: (1, 6),
    # 3(2) + 2(5) + 1 = 17
    17: (2, 5),
    # 3(1) + 2(7) + 1 = 18
    18: (1, 7),
    # 3(2) + 2(6) + 1 = 19
    19: (2, 6),
    # 3(1) + 2(8) + 1 = 20
    20: (1, 8),
    # 3(2) + 2(7) + 1 = 21
    21: (2, 7),
    # 3(1) + 2(9) + 1 = 22
    22: (1, 9),
    # 3(2) + 2(8) + 1 = 23
    23: (2, 8),
    # 3(1) + 2(10) + 1 = 24
    24: (1, 10),
    # 3(2) + 2(9) + 1 = 25
    25: (2, 9),
    # 3(1) + 2(11) + 1 = 26
    26: (1, 11),
    # 3(2) + 2(10) + 1 = 27
    27: (2, 10),
    # 3(1) + 2(12) + 1 = 28
    28: (1, 12),
    # 3(2) + 2(11) + 1 = 29
    29: (2, 11),
    # 3(1) + 2(13) + 1 = 30
    30: (1, 13)
}

# Set up Prime
def setup_prime(replica_ip:dict, num_replicas:int, max_po:int):

    # Update prime/bin/address.config
    address_conf(replica_ip)
   
    # Update prime/src/def.h
    num_f, num_k = configurations[num_replicas]
    def_h(NUM_F=num_f, NUM_K=num_k, MAX_PO=max_po)
    
    # Path to Prime
    prime_path = "../prime"

    # Build Prime
    build_prime(prime_path)

    # Handles keys for Prime
    handle_keys(prime_path,num_replicas)





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

    with open('prime_status.log', 'w') as prime_status_log:
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
            with open('prime_status.log', 'r') as log:
                print(log.read(), flush=True)
            raise RuntimeError(f'Prime exited during startup')
        else:
            # Check log file for handshake msgs
            with open('prime_status.log', 'r') as prime_status_log:
                for line in prime_status_log.readlines():
                    if 'Called PR_Resume_Normal_operations' in line:
                        time.sleep(2)
                        return prime

# Copies keys to Prime's key folder iff it does not already have them. 
def handle_keys(prime_path, num_replicas):
    # Along with other keys,prime/bin/keys has num_replicas # of keys named sharex_1.pem where x=0,1,2,3,....,num_replicas-1 
    # Use this to distinguish between which key set is being used. Check if share[0-->num_replicas-1] exists and that share[num_replicas].pem does not
    for i in range(num_replicas+1):
        path_name = prime_path+f"/bin/keys/share{i}_1.pem"

        # Mismatch, copy keys & return
        mismatch = (
            # sharei_1.pem DNE and i < num_replicas
           ( i < num_replicas and not os.path.exists(path_name))
            # sharei_1.pem Exists and i==num_replicas
            or (i==num_replicas and os.path.exists(path_name))
        )

        if mismatch:
            keys_path = prime_path+"/bin/keys"
            # Clear existing prime/bin/keys content
            subprocess.run(["rm","-rf", keys_path])
            # Make new keys dir 
            os.makedirs(keys_path,exist_ok=True)
            # Copy Prime keys for this replica count.
            subprocess.run(
                [
                    "cp", "-a",
                    f"../keys/saved_keys/prime_keys/replicas_{num_replicas}/.",
                    prime_path + "/bin/keys/",
                ],
                check=True,
            )
            return