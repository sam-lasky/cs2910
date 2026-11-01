import subprocess
import sys
import shutil
import os
# local 
sys.path.insert(0, "..")
from common.config import *

# Number of Replicas being used
replica_count= None
# Dictionary where key = replica count, value = (NUM_F,NUM_K) tuple
configs = {}

# 30 Replicas where each tuple holds (NUM_F, NUM_K) that 
# satisfies the NUM_SERVERS (3*NUM_F + 2*NUM_K + 1) equation
# in prime/src/def.h 
# (KEY:INT) Number of Replicas = (VALUE:(INT,INT)) (NUM_F, NUM_K)
configurations = {
    # num replicas = 6, NUM_F=1, NUM_K=1
    6: (1, 1),
    # num replicas = 7, NUM_F=2, NUM_K=0
    7: (2, 0),
    # num replicas = 8, NUM_F=1, NUM_K=2
    8: (1, 2),
    # num replicas = 9, NUM_F=2, NUM_K=1
    9: (2, 1),
    # num replicas = 10, NUM_F=1, NUM_K=3
    10: (1, 3),
    # num replicas = 11, NUM_F=2, NUM_K=2
    11: (2, 2),
    # num replicas = 12, NUM_F=1, NUM_K=4
    12: (1, 4),
    # num replicas = 13, NUM_F=2, NUM_K=3
    13: (2, 3),
    # num replicas = 14, NUM_F=3, NUM_K=2
    14: (3, 2),
    # num replicas = 15, NUM_F=2, NUM_K=4
    15: (2, 4),
    # num replicas = 16, NUM_F=1, NUM_K=6
    16: (1, 6),
    # num replicas = 17, NUM_F=2, NUM_K=5
    17: (2, 5),
    # num replicas = 18, NUM_F=1, NUM_K=7
    18: (1, 7),
    # num replicas = 19, NUM_F=2, NUM_K=6
    19: (2, 6),
    # num replicas = 20, NUM_F=1, NUM_K=8
    20: (1, 8),
    # num replicas = 21, NUM_F=2, NUM_K=7
    21: (2, 7),
    # num replicas = 22, NUM_F=1, NUM_K=9
    22: (1, 9),
    # num replicas = 23, NUM_F=2, NUM_K=8
    23: (2, 8),
    # num replicas = 24, NUM_F=1, NUM_K=10
    24: (1, 10),
    # num replicas = 25, NUM_F=2, NUM_K=9
    25: (2, 9),
    # num replicas = 26, NUM_F=1, NUM_K=11
    26: (1, 11),
    # num replicas = 27, NUM_F=2, NUM_K=10
    27: (2, 10),
    # num replicas = 28, NUM_F=1, NUM_K=12
    28: (1, 12),
    # num replicas = 29, NUM_F=2, NUM_K=11
    29: (2, 11),
    # num replicas = 30, NUM_F=1, NUM_K=13
    30: (1, 13)
}

# Generates keys using the passed NUM_F/K values. 
# Updates prime/src/def.h using these values
# Stores the generated keys in CS2910/keys/prime_keys
def gen_keys(NUM_F, NUM_K ):

    # Update NUM_F/K vals in prime/src/def.h
    def_h(NUM_F,NUM_K,20)

    # Make clean Prime
    subprocess.run(["make", "clean"], cwd="prime/src", check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Make Prime
    subprocess.run(["make"], cwd="prime/src", check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Generate keys
    subprocess.run(["./gen_keys"], cwd="prime/bin", check=True)

    # Make a subdirectory for the generated keys
    os.makedirs(f'prime_keys/{replica_count}_keys')

    # Copy the generated keys to this directory
    subprocess.run(["cp", "-r", "prime/bin/keys", f"prime_keys/replicas_{replica_count}/"], check=True)


# Generates replica_count number of distinct NUM_F/NUM_K comboniations
# which satisfy the equation NUM_SERVERS=(3*NUM_F + 2*NUM_K+1) in prime/src/def.h
def config_generator():
    global configurations
    for replica_num in range(6,replica_count+1):
        for num_f in range(1,101):
            for num_k in range(0,101):
                if (3*num_f)+(2*num_k)+1 == replica_num:
                    configurations[replica_num]=(num_f,num_k)
                    break
            if replica_num in configurations:break
        if replica_num in configurations:break
        else: raise RuntimeError(f'Cannot generate (NUM_F, NUM_K pair) for {replica_count} # of replicas')
        
# Generate <replica_count> distinct # of keys for Prime, store them in keys/prime_keys/[replica_num]_keys
def gen_prime_keys():

    # Make the keys directory in the root cs2910 file, replace it if it already exists
    if os.path.exists("prime_keys"):
        shutil.rmtree("prime_keys")
    os.makedirs("prime_keys")

    # Generate the configurations
    config_generator()

    # Generate all keys for number of replicas 6 --> 30
    for config in configurations:
        num_f = config[0]
        num_k = config[1]
        print(f'GENERATING KEYS FOR {replica_count}')
        gen_keys(num_f,num_k)

# Generate <replica_count> distinct # of keys for Spines, store them in keys/spines_keys/[replica_num]_keys
def gen_spines_keys():
    # Make the keys directory in the root cs2910 file, replace it if it already exists
    if os.path.exists("spines_keys"):
        shutil.rmtree("spines_keys")
    os.makedirs("spines_keys")

    # Dir that temporarily stores generated keys
    os.makedirs("spines_keys/temp")

    # Create all subdirectories for each replica count, 
    for i in range(6,replica_count+1):
        os.makedirs(f"spines_keys/{i}_replicas")

    # dhparam keygen subprocess, can be used across different configs, make once & copy it to every dir
    subprocess.run(
        [
            "openssl", "dhparam",
            "-outform", "PEM",
            "-out", "spines_keys/temp/dhparam.pem",
            "2048",
        ],
        check=True,
    )

    # Generate public/private keys in range 1-->replica_count
    for i in range(1,replica_count + 1):
        # private
        subprocess.run(
            [
                "openssl", "genrsa",
                "-out", f"spines_keys/temp/private{i}.pem",
                "1024",
            ],
            check=True,
        )
        # public
        subprocess.run(
            [
                "openssl", "rsa",
                "-in", f"spines_keys/temp/private{i}.pem",
                "-out", f"spines_keys/temp/public{i}.pem",
                "-outform", "PEM",
                "-pubout",
            ],
            check=True,
        )

    # Copy the keys into each replica directory
    for i in range(6,replica_count+1):
        # Copy dhparam.pem
        subprocess.run("cp","spines_keys/temp/dhparam.pem","spines_keys/")
        # copy all priv/pub keys into the curr rep count subdirectory
        for i in range(1,replica_count+1):
            subprocess.run("cp", f"spines_keys/temp/private{i}.pem",f"spines_keys/{i}_replicas/")
            subprocess.run("cp", f"spines_keys/temp/public{i}.pem",f"spines_keys/{i}_replicas/")

    # Delete the temporary directory
    shutil.rmtree("spines_keys/temp")

# Creates num_replicas distinct keys for key_type <prime|spines|both>
def main(key_type='all',num_replicas=20):
    global replica_count
    replica_count=num_replicas

    keys_to_generate = [gen_prime_keys, gen_spines_keys]
    # Only gen Prime keys
    if key_type=='prime':
        keys_to_generate.remove(gen_prime_keys)
    # Only gen Spines keys
    elif key_type=='spines':
        keys_to_generate.remove(gen_spines_keys)

    # Gen keys 
    for func in keys_to_generate:
        func()


if __name__ == '__main__':
    main()