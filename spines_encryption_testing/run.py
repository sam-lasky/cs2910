#!/usr/bin/env python3
"""Build and start two Spines-only containers with generated configuration."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
DOCKER = ROOT / "docker"
FILES = DOCKER / "docker_files"
COMPOSE = Path(__file__).resolve().parent / "docker-compose_base.yml"


def run(*args, cwd=None):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run([str(a) for a in args], cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--encrypted', action='store_true', help='Enable IT link crypto/encryption')
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    from common.config import spines_conf

    # Existing spines_conf uses ../prime/... relative to the working directory.
    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT / 'common')
        spines_conf({1: '172.20.0.2', 2: '172.20.0.3'}, args.encrypted)
    finally:
        os.chdir(old_cwd)

    config = ROOT / 'prime/spines/daemon/spines.conf'
    if not config.is_file():
        raise FileNotFoundError(config)

    run('docker', 'build', '-f', FILES / 'Dockerfile.base', '-t', 'base-img', ROOT)
    run('docker', 'build', '-f', FILES / 'Dockerfile.spines', '-t', 'spines-img', ROOT)
    run('docker', 'compose', '-f', COMPOSE, 'up', '-d', '--force-recreate')

    # Dockerfile.spines clones the repo, so copy the locally generated config
    # into each running container rather than relying on the cloned copy.
    for container in ('spines1', 'spines2'):
        run('docker', 'cp', config, f'{container}:/root/cs2910/prime/spines/daemon/spines.conf')

    print(f'\nReady: encryption {"ON" if args.encrypted else "OFF"}.')
    print('Start Spines daemons inside each container before running benchmarks.')


if __name__ == '__main__':
    main()
