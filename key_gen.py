import subprocess
import sys
import shutil
import os
from common.file_ops import *

# All possible configs
# Index configs[i]= (NUM_F, NUM_K, i TOTAL REPLICAS)
configurations = [
    (1, 1, 6),
    (1, 2, 7),
    (1, 2, 8),
    (2, 1, 9),
    (1, 3, 10),
    (2, 2, 11),
    (1, 4, 12),
    (2, 3, 13),
    (3, 2, 14),
    (2, 4, 15),
    (1, 6, 16),
    (2, 5, 17),
    (1, 7, 18),
    (2, 6, 19),
    (1, 8, 20),
    (2, 7, 21),
    (1, 9, 22),
    (2, 8, 23),
    (1, 10, 24),
    (2, 9, 25),
    (1, 11, 26),
    (2, 10, 27),
    (1, 12, 28),
    (2, 11, 29),
    (1, 13, 30),
]

# Generates keys using the passed NUM_F/K values. 
# Updates prime/src/def.h using these values
# Stores the generated keys in CS2910/keys_aster/replicas_i
def gen_keys(NUM_F, NUM_K, num_replicas):
    # Update prime/src/def.h using the correct NUM_F/K values
    replacement_dict = {
        '#def NUM_F':  f'#define NUM_F {NUM_F}',
        '#def NUM_K':  f'#deine NUM_K {NUM_K}',
    }
    modify_file('prime/src/def.h', replacement_dict)

    # Make clean Prime
    subprocess.run(["make", "clean"], cwd="prime/src", check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Make Prime
    subprocess.run(["make"], cwd="prime/src", check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Generate keys
    p = subprocess.run(["./gen_keys"], cwd="prime/bin")

        # os.makedirs("key_gen_dir")
    print(os.getcwd())


    exit(0)    



def change_def_h(f:int,k:int):
    with open('prime/src/def.h', 'r') as file:
        new_def_h=''
        for line in file.readlines():
            if line.startswith('#define NUM_F'):
                line=f'#define NUM_F {f}\n'
            elif line.startswith('#define NUM_K'):
                line=f'#define NUM_K {k}\n'
            new_def_h+=line 
    with open('prime/src/def.h', 'w') as file:
        file.write(new_def_h)

# Usage: python key_gen.py <L|A> <ASTER_MACHINE_NUMBER>
# Assumes LAN 1
def main():
    # Local execution
    if sys.argv[1]=='L':
        machine_number=sys.argv[2]
        p = subprocess.run([
            'ssh',
            f'sjl79@aster{machine_number}.cs.pitt.edu',
            'cd ~/cs2910 && git pull && python3 key_gen.py A 20'
            ],capture_output=True, text=True)
        print(p.stdout)
        return
   
    # *** Aster execution ***
    
    # Make the keys directory in the root cs2910 file, replace it if it already exists
    if os.path.exists("key_gen_dir"):
        shutil.rmtree("key_gen_dir")
    os.makedirs("key_gen_dir")

    # Generate all keys for number of replicas 1-->30
    for config in configurations:
        NUM_F = config[0]
        NUM_K = config[1]
        num_replicas = config[2]
        gen_keys(NUM_F, NUM_K, num_replicas)

# Index configs[i]= (NUM_F, NUM_K, i TOTAL REPLICAS)



if __name__ == '__main__':
    main()