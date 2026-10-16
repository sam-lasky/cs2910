import sys, subprocess, os, hashlib, json

# Build a Docker image using the specified Dockerfile and image name.
def build_image(docker_file, new_images: list[str]):  
    # report build start
    print(f"Building {docker_file}-img using Dockerfile.{docker_file}")
    # build the docker build command the subprocess will use 
    cmd = f"docker build --no-cache -f Dockerfile.{docker_file} -t {docker_file}-img ."
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
        print(f"Image name used: {docker_file}-img")
        exit(1)

    # append the dockerfile name to the new_images list for updating hash 
    new_images.append(docker_file)

    # report success
    print(f"Successfully built image {docker_file}-img")

    if docker_file=='base':build_image('spines',new_images)
    elif docker_file=='spines':build_image('prime',new_images)
    else:return

# Updates the hash values iff a new image was created (i.e. included in new_images)
def update_hashes(new_images):
    # hash all the docker files
    hashes = hash_files(new_images)
    # Read existing hashes
    with open('docker_hashes.txt', 'r') as f:
        lines = f.readlines()
    # Update them accordingly 
    with open('docker_hashes.txt', 'w') as f:
        for line in lines:
            if line.startswith(tuple(hashes)):
                key = line.split()[0]
                line =f'{key} {hashes[key]}\n'
            f.write(line)



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
    hashes = {}

    with open('docker_hashes.txt', 'r') as f:
        for line in f:
            line = line.split()
            if len(line) > 1 and (hash_type := line[0]) in ['base', 'spines', 'prime']:
                hashes[hash_type] = line[1]

    return hashes
    
# Generates a SHA-256 hash of the specified Docker file
def hash_files(docker_files):
    # dict that holds hashes 
    hashes={}

    # go through each file and generate a hash ('base', 'spines', 'prime' are all possible choices for docker_files)
    for file in docker_files:
        # open the docker file as bytes and compute and store its SHA-256 hash in the dict 
        with open(f'Dockerfile.{file}', 'rb') as f:
            hashes[file]=hashlib.sha256(f.read()).hexdigest()
    # return the hashes
    return hashes
# process the user build request accordingly 
def process_build_request(image_type,highest_modified):
    # tracks all new images created to update hash values
    new_images=[]

    match image_type:
        # Build the base image using Dockerfile.base
        case "base":
            build_image('base',new_images)
        # build the spines image using Dockerfile.spines
        case "spines":
            build_image('spines',new_images)
        # build the prime image using Dockerfile.prime
        case "prime":
            build_image('prime',new_images)
        # automatically construct the image(s)
        case "auto":    
            # get stored hashes 
            stored = read_stored_hash()
            # get the current hashes of all docker files 
            current = hash_files(['base', 'spines', 'prime'])

            # Required rebuild
            rebuild = None
            # Check if prime has changed 
            if highest_modified==1 or stored['prime']!=current['prime'] :rebuild='prime'
            # check if spines has changed. This requires spines and prime to be rebuilt
            if highest_modified==2 or stored['spines']!=current['spines'] :rebuild='spines'
            # check if base has changed. If it has then all other images must also be rebuilt
            if stored['base']!=current['base'] :rebuild='base'

            # Initiate rebuilds & Update hash values
            if rebuild is not None: 
                build_image(rebuild, new_images)
                update_hashes(new_images)
    
    if not new_images:
        print('No new images built!\n')



# Type of image you are trying to build:
#   (a) base   ==>  create the image using Dockerfile.base
#   (b) spines ==>  create the image using Dockerfile.spines, the previous image is required.
#   (c) prime  ==>  create the image using Dockerfile.prime, the previous images are required.
#   (d) auto   ==>  automatically rebuilds all necessary images based on any changes made/updates to the 
#                   repo
# usage: python build.py <image-type> <highest-dir-modified>
# for highest-dir-modified:
#   1: file inside prime directory modified, 2: file inside spines directory modified
def main():
    image_type = sys.argv[1]
    highest_modified = sys.argv[2]

    print('Docker: Checking if new images need to be constructed...')
    process_build_request(image_type,highest_modified)

if __name__=='__main__':
    main()