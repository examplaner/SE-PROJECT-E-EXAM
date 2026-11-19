"""The app's input checks, shown without a person. Each step does what a person
does in the inputs menu, and prints what the app says.

    python tests/app_checks.py

A file is checked on its own when it is chosen; the checks across files run
when the person continues to the exam dates.
"""

import sys
from pathlib import Path

PROTOTYPE = Path(__file__).resolve().parents[1]
# the app's modules sit in prototype3/
sys.path.insert(0, str(PROTOTYPE))

import inputs  # noqa: E402
import planner  # noqa: E402
import terminal  # noqa: E402
# planner.py has put engine/ on the path
import loader  # noqa: E402

TINY = PROTOTYPE / "data" / "tiny"
BROKEN_REGISTRATIONS = PROTOTYPE / "data" / "invalid" / "registrations_unknown_course.csv"


def continue_to_dates(selected):
    """What "Continue to exam dates" says: the checks across files."""
    try:
        planner.load_selected(selected, planner.read_settings(selected["settings"]))
    except planner.InputProblem as error:
        return str(error)
    return "accepted"


def show(step, expected, actual):
    """Print one step. Returns True if the app said what was expected."""
    print(f"\n{step}\nExpected: {expected}\nActual:\n{actual}")
    if expected in actual:
        print("PASS")
        return True
    print("FAIL")
    return False


results = []

# 1. A room list chosen as the teachers file: refused at once, because its
# header is wrong. The old choice would stay.
problem = terminal.check_input(inputs.input_named("teachers"), TINY / "rooms.csv")
results.append(show("1. Choose rooms.csv for Teachers",
                    "rooms.csv row 1: header should be teacher_id,rank",
                    problem or "accepted"))

# 2. The registrations with an unknown course: accepted when chosen, because
# the file on its own is fine. Only courses.csv knows the course is missing.
problem = terminal.check_input(inputs.input_named("registrations"), BROKEN_REGISTRATIONS)
results.append(show("2. Choose registrations_unknown_course.csv for Student course registrations",
                    "accepted", problem or "accepted"))

# 3. Every other input from data/tiny, then Continue: the checks across files
# find the unknown course on row 50, and the calendars don't open.
selected = loader.input_paths(TINY)
selected["registrations"] = BROKEN_REGISTRATIONS
results.append(show("3. Continue to exam dates",
                    "registrations_unknown_course.csv row 50: course code CSE9999 is not in "
                    "courses.csv",
                    continue_to_dates(selected)))

# 4. The right registrations file instead: Continue goes on to the calendars.
selected["registrations"] = TINY / "registrations.csv"
results.append(show("4. Choose data/tiny/registrations.csv instead, and Continue",
                    "accepted", continue_to_dates(selected)))

print(f"\n{results.count(True)}/{len(results)} app checks passed.")
if not all(results):
    sys.exit(1)
