import subprocess
import sys
import os

configurations = range(6, 21)


def gen_keys(num_replicas):
    keys_dir = f"spines_key_gen_dir/replicas_{num_replicas}/keys"
    os.makedirs(keys_dir)

    # Generate Diffie-Hellman parameters.
    subprocess.run(
        [
            "openssl", "dhparam",
            "-outform", "PEM",
            "-out", f"{keys_dir}/dhparam.pem",
            "2048",
        ],
        check=True,
    )

    # Generate each replica's private and public keys.
    for i in range(1, num_replicas + 1):
        subprocess.run(
            [
                "openssl", "genrsa",
                "-out", f"{keys_dir}/private{i}.pem",
                "1024",
            ],
            check=True,
        )

        subprocess.run(
            [
                "openssl", "rsa",
                "-in", f"{keys_dir}/private{i}.pem",
                "-out", f"{keys_dir}/public{i}.pem",
                "-outform", "PEM",
                "-pubout",
            ],
            check=True,
        )


# Usage: python3 spines_key_gen.py <L|A> <ASTER_MACHINE_NUMBER>
def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("L", "A"):
        sys.exit(
            "Usage: python3 spines_key_gen.py <L|A> <ASTER_MACHINE_NUMBER>"
        )

    mode = sys.argv[1]
    machine_number = str(int(sys.argv[2]))

    # Local execution.
    if mode == "L":
        host = f"sjl79@aster{machine_number}.cs.pitt.edu"

        subprocess.run(
            [
                "ssh",
                host,
                "cd ~/cs2910 && git pull && "
                f"python3 spines_key_gen.py A {machine_number}",
            ],
            check=True,
        )

        subprocess.run(
            ["scp", "-r", f"{host}:~/cs2910/spines_key_gen_dir", "."],
            check=True,
        )

    # Aster execution. Requires OpenSSL; no Spines build needed.
    elif mode == "A":
        for num_replicas in configurations:
            gen_keys(num_replicas)


if __name__ == "__main__":
    main()