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

bandwidths = [100, 250, 500, 750]

for encrypted in (True, False):
    mode = 'on' if encrypted else 'off'
    print(f'\n=== Encryption {mode.upper()} ===', flush=True)

    # Generate the appropriate Spines configuration.
    os.chdir(ROOT / 'common')
    spines_conf({1: '172.20.0.2', 2: '172.20.0.3'}, encrypted)
    os.chdir(ROOT)

    for bandwidth in bandwidths:
        for trial in range(1, 6):
            print(
                f'\n=== Encryption {mode.upper()} | '
                f'{bandwidth} Mbps | Trial {trial}/5 ===',
                flush=True
            )

            compose('restart')

            # Enforce the selected bandwidth on both containers.
            for name in ('spines1', 'spines2'):
                run('docker', 'exec', name, 'tc', 'qdisc', 'replace',
                    'dev', 'eth0', 'root', 'tbf',
                    'rate', f'{bandwidth}mbit',
                    'burst', '32kbit', 'latency', '400ms')

            # Copy configuration and start Spines daemons.
            for name, ip in [('spines1', '172.20.0.2'),
                             ('spines2', '172.20.0.3')]:
                run('docker', 'cp',
                    ROOT / 'prime/spines/daemon/spines.conf',
                    f'{name}:{DAEMON}/spines.conf')

                run('docker', 'exec', name, 'rm', '-f',
                    '/tmp/spines8100', '/tmp/spines8100data')

                run('docker', 'exec', '-d', '-w', DAEMON, name, 'sh', '-c',
                    f'./spines -I {ip} > /tmp/spines.log 2>&1')

            time.sleep(5)

            opts = '-P 8 -D 0 -n 1000000 -b 1000'

            # Start receiver.
            run('docker', 'exec', '-d', 'spines2', 'sh', '-c',
                f'cd {TEST} && ./sp_bflooder -v {opts} '
                f'> /tmp/receiver.log 2>&1')

            time.sleep(2)

            # Start sender at the selected bandwidth.
            run('docker', 'exec', 'spines1', 'sh', '-c',
                f'cd {TEST} && ./sp_bflooder -s {opts} '
                f'-a 172.20.0.3 -R {bandwidth * 1000}')

            time.sleep(3)

            # Save receiver results.
            filename = HERE / f'receiver-{mode}-{bandwidth}mbps-trial{trial}.log'

            with open(filename, 'w') as f:
                subprocess.run(
                    ['docker', 'exec', 'spines2', 'cat', '/tmp/receiver.log'],
                    stdout=f,
                    check=True
                )

            print(f'Saved {filename.name}', flush=True)

print('\nDone. Check the 40 receiver log files.')