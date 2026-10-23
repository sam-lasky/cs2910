import subprocess


def check_configs():
    # configs[i] = (f,k) where f = max num byzantine replicas, k = max num benign replicas
    configs = {
        6: (1, 1),
        7: (2, 0),
        8: (1, 2),
        9: (2, 1),
        10: (3, 0),
    }
    bugged_configs=[]
    for i in range(6,11):
        f = configs[i][0]
        k = configs[i][1]

        change_def(f,k)
        subprocess.run(["make", "clean"], cwd="prime/src", check=True)
        subprocess.run(["make"], cwd="prime/src", check=True)
        p = subprocess.run(["./gen_keys"], cwd="prime/bin", check=False)
        if p.returncode!=0:
            print(p.stderr)
            bugged_configs.append(i)
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