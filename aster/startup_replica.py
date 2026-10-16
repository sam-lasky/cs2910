import sys, subprocess, time, os, socket

# set up spines 
def setup_spines(machine_id):
    spines_path = "../prime/spines"
    try:

        subprocess.run(["chmod", "+x", "configure"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "+x", "stdutil/configure"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "-R", "+x", "stdutil/buildtools"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "+x", "libspread-util/configure"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "-R", "+x", "libspread-util/buildtools"], cwd=spines_path, check=True)

        print("Configuring Spines...", flush=True)
        subprocess.run(["./configure"], cwd=spines_path, check=True)

        print("Building parser...", flush=True)
        subprocess.run(["make", "-C", "daemon", "parser"], cwd=spines_path, check=True)

        print("Building Spines...", flush=True)
        subprocess.run(["make"], cwd=spines_path, check=True)

        # Copy Spines keys
        subprocess.run(
            ["cp", "-a", "../spines_keys/.", spines_path + "/daemon/keys/"],
            check=True
        )

        
        # if machine_id==13:
        #     print('Generating Spines keys...', flush=True)
        #     subprocess.run(
        #         "chmod +x gen_keys.sh && ./gen_keys.sh",
        #         cwd=spines_path + "/daemon",
        #         shell=True,
        #         check=True
        #     )

        #     # Save keys outside the cs2910 repository
        #     backup_dir = os.path.expanduser("~/spines_keys")

        #     subprocess.run(
        #         ["cp", "-a", spines_path + "/daemon/keys", backup_dir],
        #         check=True
        #     )
        # else:
        #     exit(1)
    
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", flush=True)

    finally:
        print("Spines successfully setup!", flush=True)

# set up prime 
def setup_prime(machine_id):
    prime_path = "../prime"
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
            check=True)

        subprocess.run(["make","clean"], cwd=prime_path+'/src')
        subprocess.run(["make"], cwd=prime_path+'/src')


        # Copy Prime keys
        subprocess.run(
            ["cp", "-a", "../prime_keys/.", prime_path + "/bin/keys/"],
            check=True
        )

        # if machine_id==13:
        #     print('Generating Prime keys...', flush=True)
        #     subprocess.run(
        #         ["./gen_keys"],
        #         cwd=prime_path + "/bin",
        #         check=True
        #         )

        #     # Save keys outside the cs2910 repository
        #     backup_dir = os.path.expanduser("~/prime_keys")

        #     subprocess.run(
        #         ["cp", "-a", prime_path + "/bin/keys", backup_dir],
        #         check=True
        #     )
        # else:exit(1)
        # exit(1)

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", flush=True)
        input("Press enter to exit")
        sys.exit(1)

    finally:
        print("Prime successfully setup!", flush=True)

# start spines, prime, and driver (if on replica 13)
def startup(aster_id, replica_id):
    base_ip = f'192.168.53.{aster_id+9}'

    # start spines: ./spines -I <ip address> 
    spines = subprocess.Popen(
        f"./spines -I {base_ip}",
        cwd='../prime/spines/daemon',
        shell=True
    )

    print("Giving spines time to start...")
    time.sleep(10)

    # start prime: ./prime -i <server id> -g <global id>
    subprocess.Popen(
    f"./prime -i {replica_id} -g {replica_id}",
    cwd='../prime/bin',
    shell=True
    )

    # wait for spines to terminate then terminate 
    spines.communicate()    

def main():
    replica_id = sys.argv[1]
    max_po = sys.argv[2]
    
    # get the aster id 
    machine_id = int(socket.gethostname().split('.')[0][5:])
    print(f'Now running on Aster {machine_id}')

    # should be in cs2910/aster - run the config to update files accordingly using config.py
    # located in '../configure' using the command line argument "aster"
    subprocess.run(
        ["python", "config.py","aster","plain",max_po],
        cwd='../configure',
        text=True)



    # update repo and only remake/setup in the event of an update
    # git_pull_msg = sys.argv[2]
    # if "Already up to date." not in git_pull_msg:
    setup_spines(machine_id)
    setup_prime(machine_id)
    # else:
    startup(machine_id,replica_id)
    
if __name__ == "__main__":
    main()        

