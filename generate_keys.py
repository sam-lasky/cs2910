import subprocess
import re
import shutil
from pathlib import Path

prime = Path("prime")
def_h = prime / "src/def.h"

configs = {
    6: (1, 1),
    7: (2, 0),
    8: (1, 2),
    9: (2, 1),
    10: (3, 0),
}

original = def_h.read_text()

try:
    for n, (f, k) in configs.items():
        print(f"Generating keys for {n} replicas...", flush=True)

        contents = re.sub(
            r"(#define NUM_F\s+)\d+",
            lambda m: m.group(1) + str(f),
            original
        )
        contents = re.sub(
            r"(#define NUM_K\s+)\d+",
            lambda m: m.group(1) + str(k),
            contents
        )

        def_h.write_text(contents)

        subprocess.run(["make", "clean"], cwd=prime / "src", check=True)
        subprocess.run(["make"], cwd=prime / "src", check=True)

        subprocess.run(["./gen_keys"], cwd=prime / "bin", check=True)

        destination = Path("saved_keys") / str(n)
        if destination.exists():
            shutil.rmtree(destination)

        shutil.copytree(prime / "bin/keys", destination)

        print(f"Saved: {destination}", flush=True)

finally:
    def_h.write_text(original)