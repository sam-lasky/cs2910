import sys, subprocess, time, os



######################################
######################################
#### configurable test parameters ####
######################################
######################################

# total number of updates a trial should send (default 25k) 
total_updates=25000
# total number of replicas used (default 6)
num_replicas=6
# bandwidth limit (default: none, 100/250/500/750 Mbps)
bandwidth_limit =  ['inf',100,250,500,750]
bandwidth_limit =  ['inf']


results_file = "results_use_this_one.txt"

# limit (in Mbps) where "inf" = no limit applied
for limit in bandwidth_limit:
    # apply the limit to all 6 replicas
    for replica_id in range(1,num_replicas+1):
        if limit!='inf':
            subprocess.run(
                f"docker exec prime{replica_id} tc qdisc replace dev eth0 root handle 1: htb default 10",
                shell=True,
                check=True
            )

            subprocess.run(
                f"docker exec prime{replica_id} tc class replace dev eth0 parent 1: classid 1:10 htb rate {limit}mbit",
                shell=True,
                check=True
            )
    # test the following number of clients
    for num_emulated_clients in [20,25,30,50,100]:
        # 3 trials per client
        for trial_num in range(1,6):
            print(f'Running trial {trial_num}, Link Speed unlimited, Num Emulated {num_emulated_clients}')

            results = subprocess.run(
            f'docker exec prime1 /root/cs2910/prime/bin/driver -l 172.20.0.2 -i 1 -s 1 -c {total_updates} -n {num_emulated_clients} -LS {0} -trialnum {trial_num}',shell=True,
            capture_output=True,
            text=True 
            )
            print("test concluded")
            time.sleep(5)

            # get the stdout from the driver program and find and parse the line with the results of the trial
            print(results.stdout, flush=True)

            with open(results_file, "a") as f:
                f.write(results.stdout)
    print('finished')