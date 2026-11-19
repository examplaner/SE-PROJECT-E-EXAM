"""Run one group of tests, to show one part of the planner in class:

    python tests/run_tests.py [group]

app-checks (the default) shows the app's input checks; impossible runs the
seven impossible datasets; every other group runs the unit tests of one part.
run_tests.sh does the same in bash.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

# prototype3/; the commands below run from here
PROTOTYPE = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

UNIT = "tests/unit/"
GROUPS = {
    "validation": [UNIT + "test_validate.py", UNIT + "test_live_checks.py"],
    "schedule": [UNIT + "test_schedule.py"],
    "seating": [UNIT + "test_seat.py"],
    "duties": [UNIT + "test_duties.py"],
    "no-plan": [UNIT + "test_no_plan.py"],
    "checker": [UNIT + "test_check.py"],
    "app": [UNIT + "test_flow.py", UNIT + "test_inputs.py", UNIT + "test_calendars.py",
            UNIT + "test_planner.py", UNIT + "test_live_checks.py"],
    "all": [UNIT],
}

# each impossible dataset and the rule its reason must name
IMPOSSIBLE_CASES = [
    ("no_exam_days", "exam days"),
    ("window_too_short", "gap"),
    ("paper_too_big", "seats"),
    ("no_day_fits", "paper placement"),
    ("waiting_paper", "duty room"),
    ("duty_room_full", "duty room"),
    ("too_few_teachers", "duties"),
]

USAGE = ("Usage: python tests/run_tests.py [group]\n"
         "Groups: app-checks (default), impossible, validation, schedule, seating, duties,\n"
         "        no-plan, checker, app, all")


def suite(files):
    """The unit tests in these files, one line per test. -B and
    no:cacheprovider keep the repo free of .pyc files and pytest's cache.
    Returns the exit code."""
    command = [PYTHON, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-v", "--tb=short"]
    return subprocess.run(command + files, cwd=PROTOTYPE).returncode


def impossible():
    """Plan each impossible dataset. Each must exit with 2, write a folder
    holding only why.txt, name its rule there, and print the same text.
    Returns the exit code."""
    passed = 0
    with tempfile.TemporaryDirectory() as work:
        for dataset, rule in IMPOSSIBLE_CASES:
            print(f"\n{dataset} (expected: exit 2, Rule: {rule}, only why.txt)")
            # text mode turns Windows' \r\n into \n, so the text compares the same
            finished = subprocess.run(
                [PYTHON, "-B", "engine/main.py", f"data/impossible/{dataset}",
                 "--output", str(Path(work) / dataset)],
                cwd=PROTOTYPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace")
            output = finished.stdout.rstrip("\n")
            print(output)
            files = list((Path(work) / dataset).glob("*/*"))
            why = ""
            if len(files) == 1 and files[0].name == "why.txt":
                why = files[0].read_text(encoding="utf-8").rstrip("\n")
            if finished.returncode == 2 and why and f"Rule: {rule}" in why and why in output:
                print("PASS")
                passed += 1
            else:
                print(f"FAIL (exit code {finished.returncode})")
    print(f"\n{passed}/{len(IMPOSSIBLE_CASES)} impossible datasets passed.")
    if passed == len(IMPOSSIBLE_CASES):
        return 0
    return 1


def main():
    if len(sys.argv) > 2:
        print(USAGE)
        return 2
    # the group to run; app-checks when none is given
    group = "app-checks"
    if len(sys.argv) == 2:
        group = sys.argv[1]

    if group == "app-checks":
        return subprocess.run([PYTHON, "-B", "tests/app_checks.py"], cwd=PROTOTYPE).returncode
    if group == "impossible":
        return impossible()
    if group in GROUPS:
        return suite(GROUPS[group])
    if group in ("-h", "--help"):
        print(USAGE)
        return 0
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
