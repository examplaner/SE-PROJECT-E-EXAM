"""Case 03: CSE2001 and CSE2003 are one question paper written by two cohorts
(constraints.yaml, same_paper).
Expected: the date sheet has 7 papers, and exactly one row holds both codes."""

from demo_helpers import PYTHON, SMALL_DATASET, expect_code, fail, new_work_folder, run

work = new_work_folder()
print("Case 03: CSE2001 and CSE2003 share one question paper.")

# Make the plan of the small dataset.
code, output = run(PYTHON, "-B", "engine/main.py", SMALL_DATASET, "--output", work / "plans")
expect_code(code, 0)
plans = list((work / "plans").iterdir())
schedule = plans[0] / "schedule.csv"

# The date sheet has a header line and one line per paper: 8 lines, 7 papers.
lines = schedule.read_text(encoding="utf-8").splitlines()
if len(lines) != 8:
    fail(f"expected 7 papers in schedule.csv, found {len(lines) - 1}")

# Only one line names either code: the shared paper is written once.
shared_rows = []
for line in lines:
    if "CSE2001" in line or "CSE2003" in line:
        shared_rows.append(line)
if len(shared_rows) != 1:
    fail("expected exactly one row for CSE2001 and CSE2003")

# Its course_codes column (the 4th) lists both codes, joined with ';'.
row = shared_rows[0]
print(f"Shared row: {row}")
date, session, paper_id, codes, students = row.split(",")
if codes != "CSE2001;CSE2003":
    fail(f"the shared row lists {codes}, expected CSE2001;CSE2003")

print("PASS: both course codes are in one paper row.")
