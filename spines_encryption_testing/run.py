#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path
import sys
import csv



ROOT= Path(__file__).resolve().parent.parent
SPINES_DAEMON_PATH = '/root/cs2910/prime/spines/daemon'
# Using sp_bflooder.c for the tests
SPINES_TEST_PROG_PATH = '/root/cs2910/prime/spines/testprogs'
ENCRYPTION_TESTING_PATH = Path(__file__).parent

# =================================================
# ==================== GLOBALS ====================
# =================================================

# Directory for the this test instance
test_run_dir = None

# Key: (bandwidth, encryption_enabled)
# Value: {trial_num: {'sender_tp': Kbps, 'receiver_tp': Kbps, 'packets_received': count}}
results_dict = {}

# Test link speeds in Mbps
link_speeds = [100,250,300,500,750]

# Encryption values (T/F)
encryption_values = [False,True]

# Total Trials per link speed/encryption val combo
total_trials= 5

# Total # packets sender container sends to receiver container
packet_count = 1000000

# Size of each packet 
packet_size = 1000

# =================================================
# =================================================

sys.path.insert(0, str(ROOT))
from common.config import spines_conf


# Helper func that executes shell commands using Py's subprocess module
def run(*args):
    return subprocess.run(
        [str(a) for a in args],
        check=True,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


# Builds the spines-img required for the containers being used
# Creates the containers & bridge net
def manage_docker(*args,build:bool=True,compose:bool=True):
    # Builds Dockerfile.spines -- installs all required dependencies, 
    # downloads the git and sets up Spines. 
    if build:run(
        'docker', 'build',
        '-f', ENCRYPTION_TESTING_PATH / 'docker_files/Dockerfile.spines',
        '-t', 'spines-img', ROOT
    )

    # Creates sender/2 containers & creates spines-net bridge network & remaining args in *args
    if compose:run(
        'docker', 'compose', '-p', 'spines-encryption',
        '-f', ENCRYPTION_TESTING_PATH / 'docker_files/docker-compose_base.yml', *args
    )


def run_tests():
    # Clear the terminal
    print('\033[2J\033[H', end='', flush=True)

    print("====================================================================================")
    print("                        STARTING TESTS                                              ")
    print("====================================================================================")


    # For each bandwidth, run Spines with encryption enabled & disabled
    for encryption_enabled in encryption_values:
        # Use bandwidths 100 Mbps, 250 Mbps, 300 Mbps, 500 Mbps, 750 Mbps
        for bandwidth in link_speeds:

            # Number of trials per bandwidth/encryption config
            for trial_num in range(1, total_trials+1):

                # timeout initially 120, grows by 30 seconds every failure 
                receiver_timeout=120

                print("\nSTATUS: CONFIGURING CONTAINERS....")

                # Failure is not an option: Recv container may never get the term packet (gets dropped)
                # and will run indefinitely. A timer is used so this does not happen, which gets incremented
                # by 30 seconds on every failure until it eventually succeeds 
                while True:
                    # Restart the containers to reset previous tc settings 
                    # and kill any leftover processes
                    manage_docker('restart',build=False)

                    # Update spines.conf on host machine (must be done multiple times due to encryption_enabled changing)
                    os.chdir(ROOT / 'common')
                    # sender: <replica_id = 1> <ip = '172.20.0.2'>
                    # receiver: <replica_id = 2> <ip = '172.20.0.3'>
                    spines_conf(
                        {1: '172.20.0.2', 2: '172.20.0.3'},
                        encryption_enabled
                    )

                    # Change dir to spines daemon dir [HOST MACHINE]
                    # os.chdir(SPINES_DAEMON_PATH)
                    os.chdir(ROOT / 'prime/spines/daemon')

                    #   (1) Copy the updated spines.conf files to the containers
                    #   (2) Apply bandwidth limits using the loop iteration's bandwidth value  
                    #   (3) Remove leftover Spines IPC socket paths leftover from previous runs/crashes
                    #       (a) /tmp/spines8100 - Control Channel
                    #       (b) /tmp/spines8100data - Data channel
                    #  
                    for container,ip in [('sender','172.20.0.2'), ('receiver','172.20.0.3')]:

                        # (1)  
                        run(
                            'docker', 'cp', 'spines.conf',
                            f'{container}:{SPINES_DAEMON_PATH}'                
                        )
                        # (2)
                        run(
                            'docker', 'exec', container,
                            'tc', 'qdisc', 'replace',
                            'dev', 'eth0', 'root', 'tbf',
                            'rate', f'{bandwidth}mbit',
                            'burst', '32kbit', 'latency', '400ms'
                        )
                        
                        # check that limit is correctly applied, if not report & terminate
                        check_limit(container, bandwidth)

                        run('docker', 'exec', container, 'tc', 'qdisc', 'show', 'dev', 'eth0')
                        
                        # (3)
                        run(
                            'docker', 'exec', container, 'rm', '-f',
                            '/tmp/spines8100', '/tmp/spines8100data'
                        )

                        # (4)
                        run(
                            'docker', 'exec', '-d', '-w', SPINES_DAEMON_PATH,
                            container, 'sh', '-c',
                            f'./spines -I {ip} > /tmp/spines.log 2>&1'
                        )


                    # Give Spines time to start
                    # print("Sleeping 10 seconds to give Spines time to start")
                    time.sleep(10)

                    '''
                        -P: Overlay Link Protocol = 8 (intrusion tolerant)
                        -D: Dissemination Algorithm = 1 (intrustion tolerant priority)
                        -n: Number of packets to sent = 1 million
                        -b: Packet size in bytes = 1,000 bytes (default value, included for readablility)
                    '''

                    opts = f"-P 8 -D 1 -n {packet_count} -b {packet_size}"

                    # receiver: Remove the receiver.log from previous runs 
                    run(
                        'docker', 'exec', 'receiver',
                        'rm', '-f', '/tmp/receiver.log'
                    )

                    # receiver: Start sp_bflooder using inputs opts CLI arguments
                    # writes log content to /root/cs2910/prime/spines/testprogs
                    receiver_process = subprocess.Popen([
                        'docker', 'exec', 'receiver', 'sh', '-c',
                        f'cd {SPINES_TEST_PROG_PATH} && ./sp_bflooder -v {opts} > /tmp/receiver.log 2>&1'
                    ])
                    # Receiver container's sp_bflooder is 

                    time.sleep(2)

                    # Print curr test config
                    status_update(bandwidth, encryption_enabled, trial_num, total_trials, packet_count, packet_size)

                    print("STATUS: CONTAINERS HAVE BEEN SUCCESSFULLY CONFIGURED!!!\n\n")

                    # sender: Start sp_bflooder using inputs opts CLI arguments
                    sender_result = subprocess.run(
                        [
                            'docker', 'exec', 'sender', 'sh', '-c',
                            f'cd {SPINES_TEST_PROG_PATH} && ./sp_bflooder -s {opts} '
                            f'-a 172.20.0.3 -R {bandwidth * 1000}'
                        ],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    # store sender's stdout to sender_output
                    sender_output = sender_result.stdout

                    # Wait for receiver to finish before accessing log (ensure all contents written)
                    # Term package may be lost, timeout = 2 minutes
                    try:
                        receiver_process.wait(timeout=receiver_timeout)
                    except subprocess.TimeoutExpired:
                        print("\n ****************** RECEIVER CONTAINER TIMED OUT ******************")                    
                        print(f"Trial {trial_num} | Bandwidth {bandwidth} | Encryption {'ENABLED' if encryption_enabled else 'DISABLED'}\n")
                        print(f"TRYING AGAIN: ATTEMPT # {   ((receiver_timeout-120) // 30) +1         }\n")
                        # increase timeout by 30 secs for next attempt
                        receiver_timeout+=30
                        print(f"THE CURRENT TIMEOUT VALUE IS: {receiver_timeout} SECONDS ! ! ! FAILURE IS NOT AN OPTION!!!!")
                        print(" ******************************************************************\n")

                        continue

                    print("All tests successful!!!")
                    # Retrives/analyzes/saves test logs (receiver)
                    # Prints results 
                    # Parses & stores receiver/sender data for later analysis 
                    handle_output(bandwidth, encryption_enabled, trial_num,sender_output)
                    break
                
        # Write results to csv using curr encrypt val 
        export_results_csv(encryption_enabled)

    
# Checks whether or not the bandwidth limit has been applied to container w/ container_name
# Terminates program if not
def check_limit(container_name:str, expected=int):
    result = subprocess.run(
        ['docker', 'exec', container_name, 'tc', 'qdisc', 'show', 'dev', 'eth0'],
        capture_output=True,
        text=True,
        check=True
    )

    if f"rate {expected}Mbit" not in result.stdout:
        raise RuntimeError(
            f"\n\nIncorrect bandwidth setting on {container_name}\n"
            f"Expected: {expected} Mbps\n"
            f"Actual: {result.stdout}"
        )
        

            

# key:(bandwidth, encryption status), value: {Trial Num:}

# Store & parse test results on host machine
def handle_output(bandwidth, encryption_enabled, trial_num,sender_output:str):

    global results_dict

    # Key to the results dict 
    key = (bandwidth, encryption_enabled)

    # If it's the 1st trial initialize this configuration in the results dictionary
    # k = (bandwidth, encryption status)
    if trial_num==1:
        results_dict[(bandwidth, encryption_enabled)]={}

    # Get the sending container's throughput (convert to Mbps)
    sender_tp = float(sender_output.split("Sender: Avg transmit rate:")[1].split()[0])/1000
    
    # Get the receiver's log and store it in stdout  
    result = subprocess.run(
        ['docker', 'exec', 'receiver', 'cat', '/tmp/receiver.log'],
        capture_output=True,
        text=True,
        check=True
    )

    # Get the receiving container's throughput (convert to Mbps)
    receiver_tp = float(result.stdout.split("- Throughput:")[1].split()[0]) / 1000
    # Get packets received 
    packets_received = int(result.stdout.split("- Num Pkts Received:")[1].split()[0])

    # Store this trial's results 
    results_dict[key][trial_num]={
        'sender_tp': sender_tp,
        'receiver_tp':receiver_tp,
        'packets_received':packets_received
    }


    # In the current test_results directory, store the log inside of log_dir (if it exists, otherwise make it first)
    log_dir = ROOT / 'spines_encryption_testing' / 'test_output' / test_run_dir / 'receiver_logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Customize log file name to the current test config 
    encryption = 'enabled' if encryption_enabled else 'disabled'
    filename = f'{bandwidth}mbps_{encryption}_trial{trial_num}.txt'    
    # Write it! 
    (log_dir / filename).write_text(result.stdout)


def status_update(bandwidth, encryption_enabled, trial_num, total_trials, packet_count, packet_size):
    config = (
        f"\nBandwidth: {bandwidth} Mbps\n"
        f"Encryption Status: {'ENABLED' if encryption_enabled else 'DISABLED'}\n"
        f"Total Packets being sent: {packet_count}\n"
        f"Packet Size: {packet_size}\n"
        f"Total Data Transmitted: {packet_count*packet_size} Bytes\n"
    )

    print(f"\n[Test Config for Trial {trial_num}/{total_trials}:"+config+"]\n",flush=True)


# Key: (bandwidth, encryption_enabled)
# Value: {trial_num: {'sender_tp': Kbps, 'receiver_tp': Kbps, 'packets_received': count}}
# results_dict = {}


# test_run_dir = None



# # Test link speeds in Mbps
# link_speeds = [100,250,300,500,750]

# # Encryption values (T/F)
# encryption_values = [True,False]

# # Total Trials per link speed/encryption val combo
# total_trials= 5

# # Total # packets sender container sends to receiver container
# packet_count = 1000000

# # Size of each packet 
# packet_size = 1000


# Export results in csv format for analysis & presentation 
def export_results_csv(encryption_status):

    # This is for the host's machine 
    output_path = ROOT / 'spines_encryption_testing' / 'test_output' / test_run_dir / f'results_{"ENCRYPTED" if encryption_status else "PLAIN"}.csv'

    # Create a csv file for the passed encryption status, use csv for ease of transition to excel 
    with open(output_path, 'w',newline='') as f:
        writer = csv.writer(f)
        # Go through every bandwidth limitation & create a table for 
        # ROW:          [Title: Bandwidth Limit Mbps, <encryption status>]
        # ROW:          [Total Packets Sent | Packet Size (Bytes) | Total Data Sent (GB)]
        # COLUMN NAMES: [Trial | Sender Throughput (Mbps) | Receiver Throughput (Mbps) | Utilization (%) | Packets Received | Delivery (%)]
        for bandwidth in link_speeds:

            # Bandwidth/encryption title (single csv cell/row in excel tbl)
            writer.writerow([f'{bandwidth} Mbps | Encryption {"ENABLED" if encryption_status else "DISABLED"} | Total Trials: {total_trials}'])

            # Test configuration (single CSV cell /row in excel tbl)
            writer.writerow([f'Total Packets Sent: {packet_count:,} | Packet Size: {packet_size:,} Bytes | Total Data Sent: {packet_count * packet_size / 1e9:g} GB'])

            # Column names
            writer.writerow([
                'Trial',
                'Sender Throughput (Mbps)',
                'Receiver Throughput (Mbps)',
                'Utilization (%) Sender',
                'Utilization (%) Receiver',
                'Packets Received',
                'Delivery (%)'
            ])

            # Get trials for the current (bandwidth, encryption) config 
            trials:dict = results_dict[(bandwidth, encryption_status)]
            # Go through each trial (ascending) & write the row
            # avg sender throughput for the current config (Mbps)
            avg_st = 0
            # avg receiver throughput for the current config (Mbps)
            avg_rt = 0
            # avg utilization % for receiver for current config
            avg_util_rec = 0
            # avg utilization % for sender for current config 
            avg_util_send = 0
            # avg pkts received for current config
            avg_rec = 0
            # avg delivery % for current config
            avg_delivery = 0

            for trial_num, data in sorted(trials.items()):
                # sender throughput in Mbps
                sender_tp = data['sender_tp']
                # receiver throughput in Mbps
                receiver_tp = data['receiver_tp']
                # packets received (receiver container)
                packets_received = data['packets_received']

                # calc utilization percentages
                util_rec = (receiver_tp/bandwidth)*100
                util_send = (sender_tp/bandwidth)*100

                # calc delivery % 
                delivery = (packets_received/packet_count)*100

                # Write row for curr trial
                writer.writerow([
                    trial_num,
                    round(sender_tp, 2),
                    round(receiver_tp, 2),
                    round(util_send, 2),
                    round(util_rec, 2),
                    packets_received,
                    round(delivery, 2)
                ])

                # update avgs 
                avg_st += sender_tp
                avg_rt += receiver_tp
                avg_util_rec += util_rec
                avg_util_send += util_send
                avg_rec += packets_received
                avg_delivery += delivery

            # Finalize avgs  
            avg_st /= total_trials
            avg_rt /= total_trials
            avg_util_rec /= total_trials
            avg_util_send /= total_trials
            avg_rec /= total_trials
            avg_delivery /= total_trials

            # Write avgs (own row) 
            writer.writerow([
            'AVERAGE',
            round(avg_st, 2),
            round(avg_rt, 2),
            round(avg_util_send, 2),
            round(avg_util_rec, 2),
            round(avg_rec, 2),
            round(avg_delivery, 2)
             ])
             # Separate bandwidth tables     
            writer.writerow([]) 

def main():
    # Make a uniquely named subdirectory in test_output for this test 

    os.chdir(ROOT / 'spines_encryption_testing' / 'test_output')
    for i in range(1,500000):
        if not os.path.exists(f'test_results_{i}'):
            global test_run_dir
            test_run_dir=f'test_results_{i}'
            os.mkdir(test_run_dir)
            break
    os.chdir('..')
    manage_docker('up', '-d', '--force-recreate')
    run_tests()

if __name__=='__main__':
    main()