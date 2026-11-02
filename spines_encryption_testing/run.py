#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path
from sys import path




ROOT= Path(__file__).parent.parent
SPINES_DAEMON_PATH = '/root/cs2910/prime/spines/daemon'
# Using sp_bflooder.c for the tests
SPINES_TEST_PROG_PATH = '/root/cs2910/prime/spines/testprogs'
ENCRYPTION_TESTING_PATH = Path(__file__).parent

path.insert(0, str(ROOT))

from common.config import spines_conf


# Helper func that executes shell commands using Py's subprocess module
def run(*args):
    return subprocess.run([str(a) for a in args], check=True, text=True)

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

    # link_speeds = [100,250,300,500,750]
    link_speeds = [100]
    encryption_values = [True]
    # encryption_values = [True,False]

    # Use bandwidths 100 Mbps, 250 Mbps, 300 Mbps, 500 Mbps, 750 Mbps
    for bandwidth in [100,250,300,500,750]:
        # For each bandwidth, run Spines with encryption enabled & disabled
        for encryption_enabled in [True, False]:

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
            os.chdir(SPINES_DAEMON_PATH)
           
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
            time.sleep(10)

            '''
                -P: Overlay Link Protocol = 8 (intrusion tolerant)
                -D: Dissemination Algorithm = 1 (intrustion tolerant priority)
                -n: Number of packets to sent = 1 million
                -b: Packet size in bytes = 1,000 bytes (default value, included for readablility)
            '''
            opts = '-P 8 -D 1 -n 1000000 -b 1000'

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

            time.sleep(2)

            # sender: Start sp_bflooder using inputs opts CLI arguments
            run(
                'docker', 'exec', 'sender', 'sh', '-c',
                f'cd {SPINES_TEST_PROG_PATH} && ./sp_bflooder -s {opts} '
                f'-a 172.20.0.3 -R {bandwidth * 1000}'
            )

            # wait for receiver to finish before accessing log (ensure all contents written)
            # NEED TO ADD LOGIC TO HANDLE INDEFINITE WAITS 
            receiver_process.wait()


            # filename = (
            #     HERE / f'receiver-{mode}-{bandwidth}mbps-trial{trial}.log'
            # )
            # deadline = time.monotonic() + 120

#             while True:
#                 result = subprocess.run(
#                     [
#                         'docker', 'exec', 'receiver',
#                         'cat', '/tmp/receiver.log'
#                     ],
#                     capture_output=True,
#                     text=True,
#                     check=True
#                 )
#                 log = result.stdout

#                 if (
#                     '- Num Pkts Received:' in log
#                     and '- Throughput:' in log
#                 ):
#                     filename.write_text(log)
#                     print(f'Saved {filename.name}', flush=True)
#                     break

#                 if time.monotonic() >= deadline:
#                     partial = filename.with_suffix('.incomplete.log')
#                     partial.write_text(log)
#                     print(
#                         f'Timed out; saved {partial.name}. Continuing.',
#                         flush=True
#                     )
#                     break

#                 time.sleep(1)

# print('\nDone. Ran 10 trials at 750 Mbps.')


def main():
    manage_docker('up', '-d', '--force-recreate')
    run_tests()


if __name__=='__main__':
    main()