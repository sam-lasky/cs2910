import sys, subprocess, os

# Type of image you are trying to build:
#   [1] base   ==> create the image using Dockerfile.base
#   [2] spines ==> create the image using Dockerfile.spines, the previous image is required.
#   [3] prime  ==> create the image using Dockerfile.prime, the previous images are required.


if len(sys.argv) != 2:
    print("Usage: python build.py <arg>")
    print("Valid args: base, spines, prime, auto")
    sys.exit(1)

# subprocess.run(
#     ["git", "pull"],
#     cwd='../',
#     text=True)
# exit(1)


build_type = sys.argv[1]

# subprocess
p = None

match build_type:
    case "base":
        p = subprocess.Popen(
            "docker build --no-cache -f Dockerfile.base -t base-img .",
            shell=True
        )
        p.wait()

    case "spines":
        p = subprocess.Popen(
            "docker build --no-cache -f Dockerfile.spines -t spines-base .",
            shell=True
        )
        p.wait()

    case "prime":
        p = subprocess.Popen(
            "docker build --no-cache -f Dockerfile.prime -t replica-img .",
            shell=True
        )
        p.wait()

    case _:
        print(f'Unrecognized image type: {build_type}')
        print('Correct types are: base, spines prime')
        sys.exit(1)

if p is not None and p.returncode != 0:
    print(f"Error: Docker build failed with exit code {p.returncode}")