"""Case 02: a student is registered for a course that does not exist.
Expected: main.py stops with exit code 1, names the file, the row and the
unknown course code, and writes no output folder."""

import shutil

from demo_helpers import PYTHON, SMALL_DATASET, expect_code, expect_text, fail, new_work_folder, run

work = new_work_folder()
print("Case 02: add a registration for a course that does not exist.")

# Copy the small dataset, so the real one stays untouched.
shutil.copytree(SMALL_DATASET, work / "input")

# Register student BT2CSE0001 for CSE9999, which is not in courses.csv.
# "a" adds to the end of the file, as >> does in bash.
with open(work / "input" / "registrations.csv", "a", encoding="utf-8", newline="") as file:
    file.write("BT2CSE0001,CSE9999\n")

# Try to make a plan. Exit code 1 means the input is invalid.
code, output = run(PYTHON, "-B", "engine/main.py", work / "input", "--output", work / "plans")
expect_code(code, 1)
expect_text(output, "registrations.csv row")
expect_text(output, "course code CSE9999 is not in courses.csv")

# Invalid input never gets an output folder.
if (work / "plans").exists():
    fail("invalid input created an output folder")

print("PASS: the input check found the bad registration.")
