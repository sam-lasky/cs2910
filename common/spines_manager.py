import subprocess
import os
import sys
import time
import shutil
from pathlib import Path


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

    # Handle keys for Spines
    handle_keys(spines_path, num_replicas = len(replica_ip.keys()))


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

# Terminate Spines Process
def kill_spines():
    subprocess.run(["pkill", "-x", "spines"], check=False)


# Start Spines
def start_spines(replica_ip:dict, replica_id:int):

    # Kill any active Spines processes on this replica
    kill_spines()
    time.sleep(1)

    with open('spines_status.log', 'w') as spines_status_log:
        # Start the Spines Process, write stdout/err to spines_status_log
        spines = subprocess.Popen(
            ["./spines", "-I", replica_ip[replica_id]],
            cwd="../prime/spines/daemon",
            stdout=spines_status_log,
            stderr=spines_status_log
        )
        # Remove fn caller's replica_id
        handshake_replica_ids = set(replica_ip.keys())-{replica_id}

    # Loop until all handshakes are completed
    while True:
        time.sleep(1)

        if spines.poll() is not None:
            with open("spines_status.log") as log:
                print(log.read())
            raise RuntimeError("Spines exited during startup")

        with open("spines_status.log") as log:
            for line in log:
                if line.startswith("Completed handshake with"):
                    handshake_replica_ids.discard(int(line.split()[3]))

        if not handshake_replica_ids:
            return spines

# Handles keys for Spines >>TODO:UPDATE THIS SO 8 REPS ISNT HARD CODED>>
def handle_keys(spines_path, num_replicas):
    # Directory containing pre-generated keys for this replica count
    source = Path(f"../keys/spines_keys/replicas_{num_replicas}")

    # Active Spines keys directory
    destination = Path(spines_path) / "daemon/keys"

    if not source.is_dir():
        raise FileNotFoundError(f"Missing Spines keys: {source}")

    # Expected key files
    expected = {
        f"{key_type}{i}.pem"
        for i in range(1, num_replicas + 1)
        for key_type in ("private", "public")
    }
    expected.add("dhparam.pem")

    # Validate generated keys
    if not expected.issubset({p.name for p in source.iterdir()}):
        raise RuntimeError(f"Incomplete Spines keys: {source}")

    # Replace active keys with the correct configuration
    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(source, destination)


