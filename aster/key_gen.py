import subprocess
import sys
import shutil

def check_configs():
    # configs[TOTAL_REPLICAS] = (f,k) where f = max num byzantine replicas, k = max num benign replicas
    # NUM_SERVERS = (3*NUM_F + 2*NUM_K + 1)
    configs = {
        6: [(1, 1)],
        7: [(1, 2)],
        8: [(1, 2)],
        9: [(2, 1)],
        10: [(1, 3)],
        11: [(2, 2)],
        12: [(1, 4)],
        13: [(2, 3)],
        14: [(3, 2)],
        15: [(2, 4)],
        16: [(1, 6)],
        17: [(2, 5)],
        18: [(1, 7)],
        19: [(2, 6)],
        20: [(1, 8)],
        21: [(2, 7)],
        22: [(1, 9)],
        23: [(2, 8)],
        24: [(1, 10)],
        25: [(2, 9)],
        26: [(1, 11)],
        27: [(2, 10)],
        28: [(1, 12)],
        29: [(2, 11)],
        30: [(1, 13)],
    }



    bugged_configs={}
    # go through 
    for i in range(6,31):
        for config in configs[i]:
            f=config[0]
            k=config[1]
            # update def.h
            change_def(f,k)
            # make clean (prime)
            subprocess.run(["make", "clean"], cwd="prime/src", check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # make prime
            subprocess.run(["make"], cwd="prime/src", check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # gen keys
            p = subprocess.run(["./gen_keys"], cwd="prime/bin")

            # seg fault
            if p.returncode==-11:
                print(f"Segmentation fault (core dumped) — {i} replicas")
                bugged_configs.setdefault(i, []).append((f, k))

    print(f'ALL BUGGED CONFIGS:{bugged_configs}')
        



def change_def(f:int,k:int):
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
    subprocess.run(['ssh',f'sjl79@aster{sys.argv[1]}.cs.pitt.edu'])
    print('we are connected')
    exit(0)
    check_configs()

if __name__ == '__main__':
    main()