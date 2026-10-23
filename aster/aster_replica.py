import sys, subprocess, time, os, socket

replica_id=None
aster_id=None

# set up spines 
def setup_spines():
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

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", flush=True)
        exit(1)

    finally:
        print("Spines successfully setup!", flush=True)

# set up prime 
def setup_prime():
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

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", flush=True)
        input("Press enter to exit")
        sys.exit(1)

    finally:
        print("Prime successfully setup!", flush=True)

# start spines, prime, and driver (if on replica 13)
def startup(aster_id, replica_id):

    LAN = '53' if '1' in os.environ['ENVIRONMENT'] else '54'
    base_ip = f'192.168.{LAN}.{aster_id+9}'

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
    global replica_id, aster_id
    # unique identifier of this replica instance
    replica_id = sys.argv[1]
    # aster machine id
    aster_id = sys.argv[2]

    # should be in cs2910/aster - run the config to update files accordingly using config.py
    # located in '../configure' using the command line argument "aster"
    subprocess.run(
        ["python", "config.py"],
        cwd='../configure',
        text=True,
        check=True)


    setup_spines(aster_id)
    setup_prime(aster_id)


    startup(aster_id,replica_id)
    
if __name__ == "__main__":
    main()        

