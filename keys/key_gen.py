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
configurations = {}

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
    for replica_num in configurations:
        num_f = configurations[replica_num][0]
        num_k = configurations[replica_num][1]
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

# Creates <num_replicas> distinct keys for key_type <prime|spines|both>
def main(key_type='all',num_replicas=20):
    global replica_count
    replica_count=num_replicas

    print(key_type)
    exit(0)

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