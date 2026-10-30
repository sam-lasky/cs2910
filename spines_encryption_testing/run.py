#!/usr/bin/env python3
"""Build Spines-only Docker containers and benchmark encryption OFF vs ON."""
import argparse
import csv
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
COMPOSE = HERE / 'docker-compose_base.yml'
DAEMON_DIR = '/root/cs2910/prime/spines/daemon'
TEST_DIR = '/root/cs2910/prime/spines/testprogs'
HOSTS = {1: '172.20.0.2', 2: '172.20.0.3'}


def run(*cmd, capture=False, timeout=None):
    cmd = [str(x) for x in cmd]
    print('+', ' '.join(cmd), flush=True)
    return subprocess.run(cmd, check=True, text=True,
                          capture_output=capture, timeout=timeout)


def docker(*args, **kwargs):
    return run('docker', *args, **kwargs)


def compose(*args):
    return docker('compose', '-p', 'spines-encryption', '-f', COMPOSE, *args)


def generate_config(encrypted):
    sys.path.insert(0, str(ROOT))
    from common.config import spines_conf
    original = Path.cwd()
    try:
        os.chdir(ROOT / 'common')
        spines_conf(HOSTS, encrypted)
    finally:
        os.chdir(original)
    config = ROOT / 'prime/spines/daemon/spines.conf'
    data = config.read_text()
    # Use IT links for encryption, but ordinary min-weight routing (not IT flooding).
    data, count = re.subn(r'(?m)^\s*IT_IntrusionToleranceMode\s*=.*$',
                          'IT_IntrusionToleranceMode = Yes', data)
    if count != 1:
        raise RuntimeError('Could not locate IT_IntrusionToleranceMode in spines.conf')
    config.write_text(data)
    return config


def exec_shell(container, shell, detached=False, capture=False, timeout=None):
    flags = ['-d'] if detached else []
    return docker('exec', *flags, '-w', DAEMON_DIR, container,
                  'sh', '-c', shell, capture=capture, timeout=timeout)


def stop_processes():
    for name in ('spines1', 'spines2'):
        exec_shell(name, 'pkill -x sp_bflooder || true; pkill -x spines || true')


def test_mode(encrypted, count, rate, size, timeout):
    label = 'on' if encrypted else 'off'
    print(f'\n=== Encryption {label.upper()} ===', flush=True)
    stop_processes()
    config = generate_config(encrypted)
    for name in ('spines1', 'spines2'):
        docker('cp', config, f'{name}:{DAEMON_DIR}/spines.conf')
    for name, ip in (('spines1', HOSTS[1]), ('spines2', HOSTS[2])):
        exec_shell(name, f'cd {DAEMON_DIR} && ./spines -I {ip} > /tmp/spines.log 2>&1', detached=True)
    time.sleep(5)
    # -P 8 selects the link implementation controlled by IT_LinkEncrypt.
    # -D 0 uses min-weight routing, not intrusion-tolerant flooding.
    opts = f'-P 8 -D 0 -n {count} -b {size}'
    exec_shell('spines2', f'cd {TEST_DIR} && ./sp_bflooder -v {opts} > /tmp/receiver-{label}.log 2>&1', detached=True)
    time.sleep(2)
    try:
        result = exec_shell('spines1',
            f'cd {TEST_DIR} && ./sp_bflooder -s -v {opts} -a {HOSTS[2]} -R {rate}',
            capture=True, timeout=timeout)
        print(result.stdout)
        # Allow the receiver to finish and flush statistics.
        time.sleep(3)
        recv = exec_shell('spines2', f'cat /tmp/receiver-{label}.log', capture=True)
        print('RECEIVER OUTPUT:\n' + recv.stdout)
        (HERE / f'sender-{label}.log').write_text(result.stdout + result.stderr)
        (HERE / f'receiver-{label}.log').write_text(recv.stdout)
        rates = re.findall(r'rate\(Mbps\):\s*([\d.]+)', recv.stdout)
        return rates[-1] if rates else 'see receiver log'
    except subprocess.TimeoutExpired:
        print(f'Timed out after {timeout}s. Check docker exec spines1 cat /tmp/spines.log')
        return 'timeout'

def main():
    parser = argparse.ArgumentParser(description='Compare Spines throughput with encryption off and on')
    parser.add_argument('--count', type=int, default=100000)
    parser.add_argument('--rate', type=int, default=100000)
    parser.add_argument('--size', type=int, default=1000)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()

    docker('build', '-f', ROOT / 'docker/docker_files/Dockerfile.base', '-t', 'base-img', ROOT)
    docker('build', '-f', ROOT / 'docker/docker_files/Dockerfile.spines', '-t', 'spines-img', ROOT)
    compose('up', '-d', '--force-recreate')
    results = []
    for encrypted in (False, True):
        throughput = test_mode(encrypted, args.count, args.rate, args.size, args.timeout)
        results.append({'encryption': 'on' if encrypted else 'off', 'throughput_mbps': throughput})
    with (HERE / 'results.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['encryption', 'throughput_mbps'])
        writer.writeheader()
        writer.writerows(results)
    print('\nResults saved to', HERE / 'results.csv', flush=True)


if __name__ == '__main__':
    main()
