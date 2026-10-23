import subprocess
import shutil

def check_configs():
    # configs[TOTAL_REPLICAS] = (f,k) where f = max num byzantine replicas, k = max num benign replicas
    # NUM_SERVERS = (3*NUM_F + 2*NUM_K + 1)
    configs = {
        4: [(1, 0)],
        5: [],
        6: [(1, 1)],
        7: [(1, 2), (2, 0)],
        8: [(1, 2)],
        9: [(2, 1)],
        10: [(1, 3), (3, 0)],
        11: [(2, 2)],
        12: [(1, 4), (3, 1)],
        13: [(2, 3), (4, 0)],
        14: [(3, 2)],
        15: [(2, 4), (4, 1)],
        16: [(1, 6), (3, 3), (5, 0)],
        17: [(2, 5), (4, 2)],
        18: [(1, 7), (3, 4), (5, 1)],
        19: [(2, 6), (4, 3), (6, 0)],
        20: [(1, 8), (3, 5), (5, 2)],
        21: [(2, 7), (4, 4), (6, 1)],
        22: [(1, 9), (3, 6), (5, 3), (7, 0)],
        23: [(2, 8), (4, 5), (6, 2)],
        24: [(1, 10), (3, 7), (5, 4), (7, 1)],
        25: [(2, 9), (4, 6), (6, 3), (8, 0)],
        26: [(1, 11), (3, 8), (5, 5), (7, 2)],
        27: [(2, 10), (4, 7), (6, 4), (8, 1)],
        28: [(1, 12), (3, 9), (5, 6), (7, 3), (9, 0)],
        29: [(2, 11), (4, 8), (6, 5), (8, 2)],
        30: [(1, 13), (3, 10), (5, 7), (7, 4), (9, 1)],
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


def main():
    check_configs()

if __name__ == '__main__':
    main()