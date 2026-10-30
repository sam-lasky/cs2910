#!/usr/bin/env python3
"""Compare Spines throughput: encrypted first, then unencrypted, at 100 Mbps offered load."""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
DAEMON = '/root/cs2910/prime/spines/daemon'
TEST = '/root/cs2910/prime/spines/testprogs'
IPS = {1: '172.20.0.2', 2: '172.20.0.3'}


def cmd(*args, capture=False):
    print('+', ' '.join(map(str, args)), flush=True)
    return subprocess.run([str(a) for a in args], check=True, text=True,
                          capture_output=capture, timeout=180 if capture else None)


def compose(*args):
    return cmd('docker', 'compose', '-p', 'spines-encryption',
               '-f', HERE / 'docker-compose_base.yml', *args)


sys.path.insert(0, str(ROOT))
from common.config import spines_conf

cmd('docker', 'build', '-f', ROOT / 'docker/docker_files/Dockerfile.base', '-t', 'base-img', ROOT)
cmd('docker', 'build', '-f', ROOT / 'docker/docker_files/Dockerfile.spines', '-t', 'spines-img', ROOT)
compose('up', '-d', '--force-recreate')

for encrypted in (True, False):
    label = 'ON' if encrypted else 'OFF'
    print(f'\n=== ENCRYPTION {label} (100 Mbps target) ===', flush=True)

    # Existing generator uses paths relative to common/.
    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT / 'common')
        spines_conf(IPS, encrypted)
    finally:
        os.chdir(old_cwd)

    config = ROOT / 'prime/spines/daemon/spines.conf'
    text = config.read_text()
    text, n = re.subn(r'(?m)^IT_IntrusionToleranceMode\s*=.*$',
                      'IT_IntrusionToleranceMode = Yes', text)
    if n != 1:
        raise RuntimeError('IT_IntrusionToleranceMode not found in spines.conf')
    config.write_text(text)

    compose('restart')  # Stops daemons and test processes from the previous run.
    for name, ip in (('spines1', IPS[1]), ('spines2', IPS[2])):
        cmd('docker', 'cp', config, f'{name}:{DAEMON}/spines.conf')
        cmd('docker', 'exec', name, 'rm', '-f', '/tmp/spines8100', '/tmp/spines8100data')
        cmd('docker', 'exec', '-d', '-w', DAEMON, name, 'sh', '-c',
            f'./spines -I {ip} > /tmp/spines.log 2>&1')
    time.sleep(5)

    # -P 8: IT link (where IT_LinkEncrypt applies); -D 0: min-weight routing.
    opts = '-P 8 -D 0 -n 100000 -b 1000'
    cmd('docker', 'exec', '-d', 'spines2', 'sh', '-c',
        f'cd {TEST} && ./sp_bflooder -v {opts} > /tmp/receiver.log 2>&1')
    time.sleep(2)
    cmd('docker', 'exec', 'spines1', 'sh', '-c',
        f'cd {TEST} && ./sp_bflooder -s {opts} -a {IPS[2]} -R 100000')
    time.sleep(3)
    output = cmd('docker', 'exec', 'spines2', 'cat', '/tmp/receiver.log', capture=True).stdout
    (HERE / f'receiver-{label.lower()}.log').write_text(output)
    rates = re.findall(r'rate\(Mbps\):\s*([\d.]+)', output)
    print(f'Encryption {label}: receiver reported {rates[-1] if rates else "no throughput sample"} Mbps')

print('\nReceiver logs saved in spines_encryption_testing/.')
