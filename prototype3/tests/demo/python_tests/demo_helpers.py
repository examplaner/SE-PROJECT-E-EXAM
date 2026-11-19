"""The start every Python demo case shares, the same as setup.bash for the bash
cases. Each case imports it."""

import atexit
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Work from prototype3/, whatever folder the case was started from, so the
# cases can name engine/main.py, engine/check.py and data/ directly.
PROTOTYPE = Path(__file__).resolve().parents[3]
os.chdir(PROTOTYPE)

# The datasets the cases use.
# 16 students, 3 rooms, one week: small enough to check by hand.
SMALL_DATASET = Path("data/tiny")
# 1,600 students, 36 rooms, three weeks.
REALISTIC_DATASET = Path("data/main")

# The Python to run: the one running this case.
PYTHON = sys.executable


def new_work_folder():
    """A new empty folder for the case's plans and copied inputs. It is
    deleted when the case ends, whether it passes or fails."""
    folder = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    return folder


def fail(message):
    """Say why the case failed and stop with exit code 1."""
    print(f"FAIL: {message}")
    sys.exit(1)


def run(*command):
    """Run a command and show what it printed. Returns (exit code, printed
    text). Text mode turns Windows' \\r\\n into \\n, so the text checks work
    the same on every system. The cases run Python with -B, so it writes no
    .pyc files into the repo."""
    parts = [str(part) for part in command]
    print()
    print("$ " + " ".join(parts))
    # stderr goes into the same text as stdout, as 2>&1 does in bash;
    # errors="replace" keeps a character Windows can't decode from crashing
    # the case
    finished = subprocess.run(parts, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              encoding="utf-8", errors="replace")
    output = finished.stdout
    print(output.rstrip("\n"))
    print(f"Exit code: {finished.returncode}")
    return finished.returncode, output


def expect_code(code, expected):
    """The command gave the expected exit code."""
    if code != expected:
        fail(f"exit code {code}, expected {expected}")


def expect_text(output, text):
    """The command printed this text."""
    if text not in output:
        fail(f"missing text: {text}")


def read_lines(path):
    """The lines of a file, each with its own line end. newline="" keeps the
    line ends as they are in the file, so a changed file differs only where
    the case changed it."""
    with open(path, encoding="utf-8", newline="") as file:
        return file.readlines()


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.writelines(lines)


def expect_one_line(text, path):
    """Exactly one line of the file holds the text, so the change a case
    makes to the file is the change it means to make."""
    count = 0
    for line in read_lines(path):
        if text in line:
            count += 1
    if count != 1:
        fail(f"expected '{text}' on exactly one line of {path}")


def replace_in_file(path, old, new):
    """Change old into new everywhere in the file, as the bash cases do
    with sed."""
    lines = []
    for line in read_lines(path):
        lines.append(line.replace(old, new))
    write_lines(path, lines)


def delete_line(path, start):
    """Delete every line of the file that starts with `start`."""
    lines = []
    for line in read_lines(path):
        if not line.startswith(start):
            lines.append(line)
    write_lines(path, lines)
