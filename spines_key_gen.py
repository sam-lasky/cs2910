import subprocess
import sys
import os

configurations = range(6, 21)


def gen_keys(num_replicas):
    daemon_dir = "prime/spines/daemon"
    script_path = f"{daemon_dir}/gen_keys"

    # Update the Bash loop for this replica count.
    with open(script_path) as file:
        lines = file.readlines()

    for index, line in enumerate(lines):
        if line.strip().startswith("for i in {1.."):
            lines[index] = f"for i in {{1..{num_replicas}}}\n"
            break
    else:
        raise ValueError("Could not find replica loop in Spines gen_keys")

    with open(script_path, "w") as file:
        file.writelines(lines)

    # Generate Spines keys.
    subprocess.run(["bash", "-e", "./gen_keys"], cwd=daemon_dir, check=True)

    # Save this set of keys.
    output_dir = f"spines_key_gen_dir/replicas_{num_replicas}"
    os.makedirs(output_dir)
    subprocess.run(
        ["cp", "-r", f"{daemon_dir}/keys", output_dir],
        check=True,
    )


# Usage: python3 spines_key_gen.py <L|A> <ASTER_MACHINE_NUMBER>
# Assumes LAN 1.
def main():
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

    # Aster execution.
    elif mode == "A":
        for num_replicas in configurations:
            gen_keys(num_replicas)


if __name__ == "__main__":
    main()