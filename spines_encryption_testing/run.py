#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
DAEMON = '/root/cs2910/prime/spines/daemon'
TEST = '/root/cs2910/prime/spines/testprogs'

from sys import path
path.insert(0, str(ROOT))
from common.config import spines_conf

def run(*args):
    return subprocess.run([str(a) for a in args], check=True, text=True)

def compose(*args):
    run('docker', 'compose', '-p', 'spines-encryption',
        '-f', HERE / 'docker-compose_base.yml', *args)

run('docker', 'build', '-f', ROOT / 'docker/docker_files/Dockerfile.base',
    '-t', 'base-img', ROOT)
run('docker', 'build', '-f', ROOT / 'docker/docker_files/Dockerfile.spines',
    '-t', 'spines-img', ROOT)

compose('up', '-d', '--force-recreate')

# Enforce 100 Mbps bandwidth on both containers.
for name in ('spines1', 'spines2'):
    run('docker', 'exec', name, 'tc', 'qdisc', 'replace',
        'dev', 'eth0', 'root', 'tbf',
        'rate', '100mbit', 'burst', '32kbit', 'latency', '400ms')

for encrypted in (True, False):
    print(f'\n=== Encryption {"ON" if encrypted else "OFF"} ===', flush=True)

    os.chdir(ROOT / 'common')
    spines_conf({1: '172.20.0.2', 2: '172.20.0.3'}, encrypted)
    os.chdir(ROOT)

    compose('restart')

    # Docker restart resets the network configuration, so reapply the limit.
    for name in ('spines1', 'spines2'):
        run('docker', 'exec', name, 'tc', 'qdisc', 'replace',
            'dev', 'eth0', 'root', 'tbf',
            'rate', '100mbit', 'burst', '32kbit', 'latency', '400ms')

    for name, ip in [('spines1', '172.20.0.2'), ('spines2', '172.20.0.3')]:
        run('docker', 'cp', ROOT / 'prime/spines/daemon/spines.conf',
            f'{name}:{DAEMON}/spines.conf')
        run('docker', 'exec', name, 'rm', '-f',
            '/tmp/spines8100', '/tmp/spines8100data')
        run('docker', 'exec', '-d', '-w', DAEMON, name, 'sh', '-c',
            f'./spines -I {ip} > /tmp/spines.log 2>&1')

    time.sleep(5)

    opts = '-P 8 -D 0 -n 1000000 -b 1000'

    run('docker', 'exec', '-d', 'spines2', 'sh', '-c',
        f'cd {TEST} && ./sp_bflooder -v {opts} > /tmp/receiver.log 2>&1')

    time.sleep(2)

    run('docker', 'exec', 'spines1', 'sh', '-c',
        f'cd {TEST} && ./sp_bflooder -s {opts} -a 172.20.0.3 -R 100000')

    time.sleep(3)

    with open(HERE / f'receiver-{"on" if encrypted else "off"}.log', 'w') as f:
        subprocess.run(['docker', 'exec', 'spines2', 'cat', '/tmp/receiver.log'],
                       stdout=f, check=True)

print('\nDone. Check receiver-on.log and receiver-off.log.')