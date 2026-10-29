# Run Docker
def run(args_dict:dict):
    # Update the docker_compose.yml file to account for all the replicas used
    build_compose_file(args_dict['num_replicas'])
    print('compose buil')

# Expand docker_compose_base.yml into docker_compose.yml by including all the required
# number of replicas 
def build_compose_file(num_replicas:int):
    new_compose=''

    for replica_num in range(1,num_replicas+1):
        # fill in compose template
        compose_template ='\n'+"""\
        prime{i}:
            image: replica-img
            container_name: prime{i}
            cap_add:
            - NET_ADMIN
            networks:
            prime-net:
                ipv4_address: 172.20.0.{ip}
            command: python3 /root/cs2910/docker/startup.py {i}
        """
        compose_template.format(i=replica_num, ip=replica_num+1)



