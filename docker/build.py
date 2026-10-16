import sys, subprocess, os, hashlib

# Build a Docker image using the specified Dockerfile and image name.
def build_image(docker_file, image_name):
    # report build start
    print(f"Building {image_name} using Dockerfile.{docker_file}")
    # build the docker build command the subprocess will use 
    cmd = f"docker build --no-cache -f Dockerfile.{docker_file} -t {image_name} ."
    # spawn a subprocess that builds the base image
    p = subprocess.Popen(
        cmd,
        shell=True
    )
    # wait for execution to finish
    p.wait()
    # Check if successful, if not print error and terminate
    if p is not None and p.returncode != 0:
        # report failure
        print(f"Error: Docker build failed with exit code {p.returncode}")
        print(f"Docker file used: Dockerfile.{docker_file}")
        print(f"Image name used: {image_name}")
        exit(1)

    # report success
    print(f"Successfully built image {image_name}")

# Retrieve the SHA-256 hashes stored in docker_hashes.txt.
#
# Returns:
#   hashes (dict): Maps each image type to the Dockerfile hash
#                  recorded during its most recent image build.
#
#       'base':   SHA-256 hash of Dockerfile.base
#       'spines': SHA-256 hash of Dockerfile.spines
#       'prime':  SHA-256 hash of Dockerfile.prime
#
#   A value of 'NONE' indicates that no hash is currently stored.
def read_stored_hash():
    # returned dictionary {'base':}
    hashes = {}
    # open the file
    with open('docker_hashes.txt','r') as f:
        for line in f.readlines():
            line = line.split()
        if len(line)>0 and (hash_type:= line[0]) in ['base', 'spines', 'prime']:
            hashes[hash_type]=line[1]
    # return dict holding the stored hashes
    return hashes
    
# Generates a SHA-256 hash of the specified Docker file
def hash_file(docker_file):
    # open the docker file as bytes and compute and return its SHA-256 hash 
    with open(docker_file, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


# process the user build request accordingly 
def process_build_request(image_type):

    match image_type:
        # Build the base image using Dockerfile.base
        case "base":
            build_image('base','base-img')

        # build the spines image using Dockerfile.spines
        case "spines":
            build_image('spines','spines-img')
 
        # build the prime image using Dockerfile.prime
        case "prime":
            build_image('prime', 'prime-img')

        # automatically construct the image(s)
        case "auto":
            # get stored hashes
            stored = read_stored_hash()

        

    # wait for the img creation to conclude
    p.wait()
    # check for any issues

# Type of image you are trying to build:
#   [1] base   ==>  create the image using Dockerfile.base
#   [2] spines ==>  create the image using Dockerfile.spines, the previous image is required.
#   [3] prime  ==>  create the image using Dockerfile.prime, the previous images are required.
#   [4] auto   ==>  evaluates the hash values of the Dockerfiles used for the most recent 
#                   image builds (stored in docker_hashes.txt) & if these vary with the current 
#                   hash values rebuild the image to keep the most up to date version.  
#                   

def main():
    # confirm correct input
    if len(sys.argv) != 2:
        print("Usage: python build.py <arg>")
        print("Valid args: base, spines, prime, auto")
        sys.exit(1)




if __name__=='__main__':
    main()