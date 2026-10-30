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
    run(
        'docker', 'compose', '-p', 'spines-encryption',
        '-f', HERE / 'docker-compose_base.yml', *args
    )


run(
    'docker', 'build',
    '-f', HERE / 'docker_files/Dockerfile.base',
    '-t', 'base-img', ROOT
)
run(
    'docker', 'build',
    '-f', HERE / 'docker_files/Dockerfile.spines',
    '-t', 'spines-img', ROOT
)

compose('up', '-d', '--force-recreate')

for bandwidth in [100, 250, 500, 750]:
    for trial in range(1, 6):
        # Alternate which mode runs first.
        modes = (True, False) if trial % 2 else (False, True)

        for encrypted in modes:
            mode = 'on' if encrypted else 'off'
            print(
                f'\nEncryption {mode.upper()} | '
                f'{bandwidth} Mbps | Trial {trial}/5',
                flush=True
            )

            # Keep authentication enabled; toggle only encryption.
            os.chdir(ROOT / 'common')
            spines_conf({1: '172.20.0.2', 2: '172.20.0.3'}, True)
            os.chdir(ROOT)

            config_path = ROOT / 'prime/spines/daemon/spines.conf'
            config = config_path.read_text()
            setting = 'IT_LinkEncrypt = True'

            if config.count(setting) != 1:
                raise RuntimeError('Expected one IT_LinkEncrypt setting')

            config_path.write_text(
                config.replace(
                    setting,
                    f'IT_LinkEncrypt = {"True" if encrypted else "False"}'
                )
            )

            compose('restart')

            for name in ('spines1', 'spines2'):
                run(
                    'docker', 'exec', name,
                    'tc', 'qdisc', 'replace',
                    'dev', 'eth0', 'root', 'tbf',
                    'rate', f'{bandwidth}mbit',
                    'burst', '32kbit', 'latency', '400ms'
                )

            for name, ip in [
                ('spines1', '172.20.0.2'),
                ('spines2', '172.20.0.3')
            ]:
                run(
                    'docker', 'cp', config_path,
                    f'{name}:{DAEMON}/spines.conf'
                )
                run(
                    'docker', 'exec', name, 'rm', '-f',
                    '/tmp/spines8100', '/tmp/spines8100data'
                )
                run(
                    'docker', 'exec', '-d', '-w', DAEMON,
                    name, 'sh', '-c',
                    f'./spines -I {ip} > /tmp/spines.log 2>&1'
                )

            time.sleep(5)

            opts = '-P 8 -D 0 -n 1000000 -b 1000'

            run(
                'docker', 'exec', 'spines2',
                'rm', '-f', '/tmp/receiver.log'
            )
            run(
                'docker', 'exec', '-d', 'spines2', 'sh', '-c',
                f'cd {TEST} && ./sp_bflooder -v {opts} '
                '> /tmp/receiver.log 2>&1'
            )

            time.sleep(2)

            run(
                'docker', 'exec', 'spines1', 'sh', '-c',
                f'cd {TEST} && ./sp_bflooder -s {opts} '
                f'-a 172.20.0.3 -R {bandwidth * 1000}'
            )

            filename = (
                HERE / f'receiver-{mode}-{bandwidth}mbps-trial{trial}.log'
            )
            deadline = time.monotonic() + 60

            while True:
                result = subprocess.run(
                    [
                        'docker', 'exec', 'spines2',
                        'cat', '/tmp/receiver.log'
                    ],
                    capture_output=True,
                    text=True,
                    check=True
                )
                log = result.stdout

                if (
                    '- Num Pkts Received:' in log
                    and '- Throughput:' in log
                ):
                    filename.write_text(log)
                    print(f'Saved {filename.name}', flush=True)
                    break

                if time.monotonic() >= deadline:
                    partial = filename.with_suffix('.incomplete.log')
                    partial.write_text(log)
                    raise RuntimeError(
                        f'Receiver did not finish: {partial.name}'
                    )

                time.sleep(1)

print('\nDone. Saved 40 receiver logs.')