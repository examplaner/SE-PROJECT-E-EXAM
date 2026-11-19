"""Case 01: make the full plan of the realistic dataset and check all of it.
Expected: main.py writes one plan folder, and check.py finds no problem in
56 papers, 454 room files, 8,750 seats and 908 duties."""

from demo_helpers import (PYTHON, REALISTIC_DATASET, expect_code, expect_text, fail,
                          new_work_folder, run)

work = new_work_folder()
print("Case 01: make the full plan of the realistic dataset and check all of it.")

# Make the plan. Exit code 0 means a plan was written.
code, output = run(PYTHON, "-B", "engine/main.py", REALISTIC_DATASET, "--output", work / "plans")
expect_code(code, 0)

# main.py made one new folder, and it holds the date sheet.
plans = list((work / "plans").iterdir())
if len(plans) != 1 or not (plans[0] / "schedule.csv").is_file():
    fail("expected one plan folder with schedule.csv")
plan = plans[0]

# Check the plan against the same input. Exit code 0 means no rule is broken.
code, output = run(PYTHON, "-B", "engine/check.py", REALISTIC_DATASET, plan)
expect_code(code, 0)
expect_text(output, "no problems")
expect_text(output, "56 papers, 454 room files, 8750 seats, 908 duties")

print("PASS: the full plan passed the checker with the expected totals.")
