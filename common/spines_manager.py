import subprocess
import os
import sys
import time
# local imports
from common.config import spines_address_config, spines_conf

# Set up spines
def setup_spines(replica_ip:dict, encrypt:int):
    # Updates prime/bin/spines_address.config
    spines_address_config(replica_ip)
    # Update prime/spines/daemon/spines.conf
    spines_conf(replica_ip, encrypt)

    # Spines directory path
    spines_path = "../prime/spines"
    # Spines executable path
    spines_exe = spines_path+"/daemon/spines"

    # Make Spines iff it does not exist
    if not os.path.isfile(spines_exe):
        build_spines(spines_path)

    # Copy Spines keys for this replica count.
    subprocess.run(
        [
            "cp", "-a",
            f"../keys/saved_keys/spines_keys/replicas_{len(replica_ip)}/keys/.",
            spines_path + "/daemon/keys/",
        ],
        check=True,
    )



# Builds Spines:
# 1. Sets execute permissions on configure scripts and build tools.
# 2. Runs configure to prepare the build.
# 3. Builds the configuration parser.
# 4. Builds the Spines executable, libraries, and utilities.
def build_spines(spines_path):
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
    except Exception as e:
        print(f"ERROR: Spines setup failed: {type(e).__name__}: {e}", flush=True)
        sys.exit(1)


# Start Spines
def start_spines(replica_ip:dict, replica_id:int):

    with open('status.log', 'w') as status_log:
        # Start the Spines Process, write stdout/err to status_log
        spines = subprocess.Popen(
            ["./spines", "-I", replica_ip[replica_id]],
            cwd="../prime/spines/daemon",
            stdout=status_log,
            stderr=status_log
        )
        # Remove fn caller's replica_id
        handshake_replica_ids = set(replica_ip.keys())-{replica_id}

    # Loop until all handshakes are completed
    while True:
        time.sleep(1)
        # Checkup on Spines
        #   poll() return values:
        #       None: Process still executing
        #       0: Process successfully exited
        #       Nonzero int: Process exited w/ error
        if spines.poll() is not None:
            raise RuntimeError(f'Spines exited during startup')
        else:
            # Check log file for handshake msgs
            with open('status.log', 'r') as status_log:
                for line in status_log.readlines():
                    if line.startswith('Completed handshake with'):
                        handshake_replica_ids-={int(line.split()[3])}
                        if len(handshake_replica_ids)==0:
                            return spines
        


