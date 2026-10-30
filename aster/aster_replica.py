
import sys
import subprocess
import time
import os
# local 
sys.path.insert(0, "..")
from configure.config import update_files, update_def_h


# Globals
replica_id = None
machine_id = None
aster_machines_used = []
env = None
max_po = None
encrypt = None

# Set up spines
def setup_spines():
    spines_path = "../prime/spines"
    print(os.getcwd())
    return 

    try:
        subprocess.run(["chmod", "+x", "configure"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "+x", "stdutil/configure"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "-R", "+x", "stdutil/buildtools"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "+x", "libspread-util/configure"], cwd=spines_path, check=True)
        subprocess.run(["chmod", "-R", "+x", "libspread-util/buildtools"], cwd=spines_path, check=True)

        subprocess.run(
            ["./configure"],
            cwd=spines_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["make", "-C", "daemon", "parser"],
            cwd=spines_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["make"],
            cwd=spines_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Copy Spines keys
        subprocess.run(
            ["cp", "-a", "../saved_keys/spines_keys/.", spines_path + "/daemon/keys/"],
            check=True
        )

    except Exception as e:
        print(f"ERROR: Spines setup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)


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
            check=True
        )

        subprocess.run(
            ["make", "clean"],
            cwd=prime_path + "/src",
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        subprocess.run(
            ["make", "-j1"],
            cwd=prime_path + "/src",
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Copy Prime keys
        subprocess.run(
            ["cp", "-a", f'../saved_keys/prime_keys/{os.environ["NUM_REPLICAS"]}_total_reps/.', prime_path + "/bin/keys/"],
            check=True
        )

    except Exception as e:
        print(f"ERROR: Prime setup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)


# start spines and prime
def startup():
    aster_id = int(os.environ["ASTER_MACHINE_ID"])
    replica_id = int(os.environ["REPLICA_ID"])

    LAN = '53' if os.environ['ENVIRONMENT'] == 'aster_LAN_1' else '54'
    base_ip = f'192.168.{LAN}.{aster_id+9}'

    try:
        # start spines: ./spines -I <ip address>
        spines = subprocess.Popen(
            ["./spines", "-I", base_ip],
            cwd='../prime/spines/daemon',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(10)

        # Verify Spines is still running
        if spines.poll() is not None:
            raise RuntimeError(f"Spines terminated with exit code {spines.returncode}")

        # start prime: ./prime -i <server id> -g <global id>
        prime = subprocess.Popen(
            ["./prime", "-i", str(replica_id), "-g", str(replica_id)],
            cwd='../prime/bin',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # print("Giving Prime time to start...", flush=True)
        time.sleep(3)

        # Verify Prime is still running
        if prime.poll() is not None:
            raise RuntimeError(f"Prime terminated with exit code {prime.returncode}")

        # print("Prime started successfully!", flush=True)

    except Exception as e:
        print(f"ERROR: Replica startup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)

    print(f"Replica {replica_id} on Aster {aster_id} started successfully!", flush=True)

# Args: aster_replica.py <replica_id> <machine_id> <aster_machines_used> <env> <max_po> <encrypt>
def main():
    # <--- Set up global variables --->
    global replica_id, machine_id, aster_machines_used, env, max_po, encrypt
    replica_id = int(sys.argv[1])
    machine_id = int(sys.argv[2])
    aster_machines_used = list(map(int, sys.argv[3].split(',')))
    env = sys.argv[4]
    max_po = int(sys.argv[5])
    encrypt = int(sys.argv[6])

    # Print config for controller
    print(f"\n{'ASTER':<8} {'REPLICA':<10} {'ENVIRONMENT':<14} {'MAX_PO':<10} {'ENCRYPTED':<12}")
    print("-" * 54)

    for rid, mid in enumerate(aster_machines_used, start=1):
        print(f"{mid:<8} {rid:<10} {env:<14} {max_po:<10} {encrypt:<12}")

    # Sets up spines, only remakes it 
    setup_spines()
    exit(0)
    setup_prime()

    startup()

    # All setup and startup checks passed
    sys.exit(0)


if __name__ == "__main__":
    main()
