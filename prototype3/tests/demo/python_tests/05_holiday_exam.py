"""Case 05: after the plan is made, 4 November becomes a holiday.
Expected: check.py, given the changed settings, finds the paper written on
4 November (exit code 3, "Rule: exam days")."""

import shutil

from demo_helpers import (PYTHON, SMALL_DATASET, expect_code, expect_one_line, expect_text,
                          new_work_folder, replace_in_file, run)

work = new_work_folder()
print("Case 05: mark 4 November as a holiday after making the plan.")

# Make the plan of the small dataset.
code, output = run(PYTHON, "-B", "engine/main.py", SMALL_DATASET, "--output", work / "plans")
expect_code(code, 0)
plans = list((work / "plans").iterdir())
plan = plans[0]

# Copy the input and make 4 November a holiday in the copy's settings.
shutil.copytree(SMALL_DATASET, work / "input")
settings = work / "input" / "settings.yaml"
expect_one_line("holidays: []", settings)
replace_in_file(settings, "holidays: []", "holidays: [2026-11-04]")

# Check the plan against the changed input. Exit code 3 means a broken rule.
code, output = run(PYTHON, "-B", "engine/check.py", work / "input", plan)
expect_code(code, 3)
expect_text(output, "Rule: exam days")
expect_text(output, "CSE2002 is on 2026-11-04, a holiday")

print("PASS: the checker found the paper written on a holiday.")
