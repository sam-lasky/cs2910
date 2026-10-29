import subprocess
import sys
import shutil
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
def gen_keys(NUM_F, NUM_K,num_replicas):
    
    # Remove the existing keys directory
    subprocess.run(["rmdir","f","keys"],cwd='cs2910/prime/bin') 

    # # go through 
    # for i in range(6,31):
    #     for config in configs[i]:
    #         f=config[0]
    #         k=config[1]
    #         # update def.h
    #         change_def(f,k)
    #         # make clean (prime)
    #         subprocess.run(["make", "clean"], cwd="prime/src", check=True,
    #                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #         # make prime
    #         subprocess.run(["make"], cwd="prime/src", check=True,
    #                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #         # gen keys
    #         p = subprocess.run(["./gen_keys"], cwd="prime/bin")

    #         # seg fault
    #         if p.returncode==-11:
    #             print(f"Segmentation fault (core dumped) — {i} replicas")
    #             bugged_configs.setdefault(i, []).append((f, k))

    # print(f'ALL BUGGED CONFIGS:{bugged_configs}')
        



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

# Usage: python key_gen.py <ASTER_MACHINE_NUMBER>
# Assumes LAN 1
def main():

    # Connect to the aster machine where keygen will occur
    subprocess.Popen(['ssh',f'sjl79@aster{sys.argv[1]}.cs.pitt.edu'])

    # Generate all keys for number of replicas 1-->30
    gen_keys(NUM_F=1, NUM_K=1,num_replicas=1)
    exit(0)



    print('we are connected')
    exit(0)
    check_configs()

if __name__ == '__main__':
    main()