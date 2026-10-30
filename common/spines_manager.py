import subprocess
import os
import sys
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
            f"../saved_keys/spines_keys/replicas_{len(replica_ip.keys())}/keys/.",
            spines_path + "/daemon/keys/",
        ],
        check=True,
    )

    print('GROOVY BABY YEAHHHH!!!!!')
    exit(0)
 



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
