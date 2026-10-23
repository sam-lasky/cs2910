import sys, subprocess, time, os
from common.env_vars import *

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
        print(f"ERROR: Spines setup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)

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
            "chmod +x OpenTC-1.1/TC-lib-1.0/csvonfigure && "
            "chmod +x OpenTC-1.1/TC-lib-1.0/missing",
            cwd=prime_path,
            shell=True,
            check=True
        )

        print("Cleaning Prime...", flush=True)
        subprocess.run(
            ["make", "clean"],
            cwd=prime_path + "/src",
            check=True
        )

        print("Building Prime...", flush=True)
        subprocess.run(
            ["make"],
            cwd=prime_path + "/src",
            check=True
        )

        # Copy Prime keys
        subprocess.run(
            ["cp", "-a", "../prime_keys/.", prime_path + "/bin/keys/"],
            check=True
        )

    except Exception as e:
        print(f"ERROR: Prime setup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)

    print("Prime successfully setup!", flush=True)


# start spines and prime
def startup(aster_id, replica_id):
    LAN = '53' if os.environ['ENVIRONMENT'] == 'aster1' else '54'
    base_ip = f'192.168.{LAN}.{aster_id+9}'

    try:
        # start spines: ./spines -I <ip address>
        spines = subprocess.Popen(
            ["./spines", "-I", base_ip],
            cwd='../prime/spines/daemon',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("Giving Spines time to start...", flush=True)
        time.sleep(10)

        # Verify Spines is still running
        if spines.poll() is not None:
            raise RuntimeError(f"Spines terminated with exit code {spines.returncode}")

        print("Spines started successfully!", flush=True)

        # start prime: ./prime -i <server id> -g <global id>
        prime = subprocess.Popen(
            ["./prime", "-i", str(replica_id), "-g", str(replica_id)],
            cwd='../prime/bin',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("Giving Prime time to start...", flush=True)
        time.sleep(3)

        # Verify Prime is still running
        if prime.poll() is not None:
            raise RuntimeError(f"Prime terminated with exit code {prime.returncode}")

        print("Prime started successfully!", flush=True)

    except Exception as e:
        print(f"ERROR: Replica startup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)

    print(f"Replica {replica_id} on Aster {aster_id} started successfully!", flush=True)

# Args: aster_replica.py <replica_id> <machine_id> ASTER_MACHINES_USED=<value> ENVIRONMENT=<value> MAX_PO=<value> ENCRYPTED=<value>
def main():
    # <--- Set up environment variables --->
    store_env(env_var_name="REPLICA_ID", env_val=sys.argv[1])
    store_env(env_var_name="ASTER_MACHINE_ID", env_val=sys.argv[2])
    store_env(env_var_name="ASTER_MACHINES_USED", env_val=sys.argv[3].split("=", 1)[1])
    store_env(env_var_name="ENVIRONMENT", env_val=sys.argv[4].split("=", 1)[1])
    store_env(env_var_name="MAX_PO", env_val=sys.argv[5].split("=", 1)[1])
    store_env(env_var_name="ENCRYPTED", env_val=sys.argv[6].split("=", 1)[1])
    # derive num replicas from aster machines used
    store_env(env_var_name="NUM_REPLICAS", env_val=str(len(os.environ["ASTER_MACHINES_USED"].split(","))))

    # Sanity check: print all configured environment variables
    for key in ("REPLICA_ID", "ASTER_MACHINE_ID", "ASTER_MACHINES_USED", "ENVIRONMENT", "MAX_PO", "ENCRYPTED"):
        print(f"{key}={os.environ[key]}", flush=True)

    # should be in cs2910/aster - run the config to update files accordingly using config.py
    # located in '../configure'
    try:
        print("Configuring replica...", flush=True)

        subprocess.run(
            ["python3", "config.py"],
            cwd="../configure",
            check=True
        )
        print("Replica configuration successful!", flush=True)
    # config failure
    except Exception as e:
        print(f"ERROR: Replica configuration failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)

    setup_spines()
    setup_prime()

    startup(aster_id, replica_id)

    # All setup and startup checks passed
    sys.exit(0)


if __name__ == "__main__":
    main()