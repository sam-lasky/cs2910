import subprocess
import os

configurations = range(6, 31)


def gen_keys(num_replicas):
    keys_dir = f"saved_keys/spines_keys/replicas_{num_replicas}/keys"
    os.makedirs(keys_dir)

    subprocess.run(
        [
            "openssl", "dhparam",
            "-outform", "PEM",
            "-out", f"{keys_dir}/dhparam.pem",
            "2048",
        ],
        check=True,
    )

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


def main():
    for num_replicas in configurations:
        gen_keys(num_replicas)


if __name__ == "__main__":
    main()