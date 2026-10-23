import subprocess
import shutil

def check_configs():
    # configs[i] = (f,k) where f = max num byzantine replicas, k = max num benign replicas
    configs = {
        6: (1, 1),
        7: (2, 0),
        8: (1, 2),
        9: (2, 1),
        10: (3, 0),
        11: (2, 2),
        12: (3, 1),
        13: (4, 0),
        14: (3, 2),
        15: (4, 1),
        16: (5, 0),
        17: (4, 2),
        18: (5, 1),
        19: (6, 0),
        20: (5, 2),
    }
    bugged_configs=[]
    for i in range(6,11):
        f = configs[i][0]
        k = configs[i][1]

        change_def(f,k)
        subprocess.run(["make", "clean"], cwd="prime/src", check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.run(["make"], cwd="prime/src", check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p = subprocess.run(["./gen_keys"], cwd="prime/bin")
        
        if p.returncode==-11:
            print(f"Segmentation fault (core dumped) — {i} replicas")
            bugged_configs.append(i)
        elif p.returncode == 0:
            shutil.copytree("prime/bin/keys", f"saved_keys/prime_keys/{i}_total_reps", dirs_exist_ok=True)
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