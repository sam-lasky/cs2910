import subprocess
import sys
import shutil
from pathlib import Path
import os
# local 
sys.path.insert(0, "..")
from common.config import *
from common.prime_manager import setup_prime

# Number of Replicas being used
replica_count= None
# Dictionary where key = replica count, value = (NUM_F,NUM_K) tuple
configurations = {}

# Make prime_keys directory in cs2910/keys, overwriting it 
# if already there. Generate all num_f/num_k combos for all replicas
# in range 6-->replica_count & store in dictionary configuration.
# Generate the keys & store them in keys/prime_keys
def gen_prime_keys():

    # Make the keys directory in the root cs2910 file, replace it if it already exists
    if os.path.exists("prime_keys"):
        shutil.rmtree("prime_keys")
    os.makedirs("prime_keys")

    # Generate the configurations
    config_generator()

    # Generate & store keys using the generated configurations 
    compile_prime_and_generate_keys()

# Generate all the Prime keys in the range [6,replica_count]. 
# Store generated keys in cs2910/keys/prime_keys
# Distinct replica keys are stored in prime_keys/replicas_[replica_number]
def compile_prime_and_generate_keys():

    for replica_num in sorted(configurations.keys()):
        num_f = configurations[replica_num][0]
        num_k = configurations[replica_num][1]
        print(f'GENERATING KEYS FOR {replica_num}, NUM_F: {num_f} NUM_K: {num_k}')

        # Sets up Prime
        #   (1) Updates addres_conf using {1-->replica_num, 'dummy_ips'}
        #   (2) Updates def_f using hardcoded NUM_F/K values hardcoded in prime_manager.py
        #   (3) Builds prime 
        setup_prime(replica_ip={i:"dummy_ip" for i in range(1, replica_num+1)}, num_replicas=replica_num, max_po=20, keys=False)

        # Generate keys
        try:
            os.makedirs("../prime/bin/keys", exist_ok=True)
            subprocess.run(["./gen_keys"], cwd="../prime/bin", check=True,stdout=subprocess.DEVNULL ,stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            # segfault
            if e.returncode==-11:
                print(f"A segfault occurred when generating keys for {replica_num} # of replicas")
                exit(1)
            raise

        # Newly generated keys for replica_num # of replicas is located in prime's bin/keys folder, move them 
        # to cs2910/keys/prime_keys/replicas_{replica_num}
        new_keys_source = Path("../prime/bin/keys") 
        new_keys_destination = Path(f"prime_keys/replicas_{replica_num}")
        shutil.copytree(new_keys_source, new_keys_destination,dirs_exist_ok=True)

        # Success
        print(f"Keys for {replica_num} Replicas written to cs2910/keys/prime_keys/replicas_{replica_num}")


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
        if replica_num not in configurations:
            raise RuntimeError(f'Cannot generate (NUM_F, NUM_K pair) for {replica_count} # of replicas')
    
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
        os.makedirs(f"spines_keys/replicas_{i}")

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
        # private keygen
        subprocess.run(
            [
                "openssl", "genrsa",
                "-out", f"spines_keys/temp/private{i}.pem",
                "1024",
            ],
            check=True,
        )
        # public keygen
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
        subprocess.run(["cp",f"spines_keys/temp/dhparam.pem",f"spines_keys/replicas_{i}/"])
        # copy all priv/pub keys into the curr rep count subdirectory
        for j in range(1,i+1):
            shutil.copy(f"spines_keys/temp/private{j}.pem", f"spines_keys/replicas_{i}/")
            shutil.copy(f"spines_keys/temp/public{j}.pem", f"spines_keys/replicas_{i}/")

    # Delete the temporary directory
    shutil.rmtree("spines_keys/temp")

# Creates <num_replicas> distinct keys for key_type <prime|spines|both>
def main(key_type,num_replicas):
    global replica_count
    replica_count=num_replicas
  
    keys_to_generate = [gen_prime_keys, gen_spines_keys]
    # Only gen Prime keys
    if key_type=='prime':
        keys_to_generate.remove(gen_spines_keys)
    # Only gen Spines keys
    elif key_type=='spines':
        keys_to_generate.remove(gen_prime_keys)

    # Gen keys 
    for func in keys_to_generate:
        func()
    

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]))