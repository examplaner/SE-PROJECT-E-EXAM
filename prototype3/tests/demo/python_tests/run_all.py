"""Run the ten Python demo cases one after another, each in a Python of its
own, and stop at the first one that fails.

    python tests/demo/python_tests/run_all.py
"""

import subprocess
import sys
from pathlib import Path

# the case files start with their number, so sorting them gives 01 to 10
CASES = sorted(Path(__file__).resolve().parent.glob("[0-9]*.py"))


def main():
    for case in CASES:
        # flush, so this line shows before the case's own output
        print(f"\n===== {case.name}", flush=True)
        finished = subprocess.run([sys.executable, "-B", str(case)])
        if finished.returncode != 0:
            print(f"\nStopped: {case.name} failed.")
            return 1
    print(f"\nAll {len(CASES)} demo cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
