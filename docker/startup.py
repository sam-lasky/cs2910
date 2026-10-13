import sys, subprocess, time, os

# replica id 
id = int(sys.argv[1])

# replica ip address (ip = 172.20.0.[0 + replica id + 1])
ip = f'172.20.0.{id+1}'


# start spines: ./spines -I <ip address> 
spines = subprocess.Popen(
    f"./spines -I {ip}",
    cwd='/root/cs2910/prime/spines/daemon',
    shell=True
)

# give spines time to start
time.sleep(5)

# start prime: ./prime -i <server id> -g <global id>
subprocess.Popen(
    f"./prime -i {id} -g {id}",
    cwd='/root/cs2910/prime/bin',
    shell=True
)

# wait for spines to terminate then terminate 
spines.communicate()