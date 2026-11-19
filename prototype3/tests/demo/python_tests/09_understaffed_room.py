"""Case 09: one of the two invigilators of room S01 is taken off duty.
Expected: check.py finds a room with too few teachers (exit code 3,
"Rule: teachers per room") and names the room and who is left."""

from demo_helpers import (PYTHON, SMALL_DATASET, delete_line, expect_code, expect_one_line,
                          expect_text, new_work_folder, run)

work = new_work_folder()
print("Case 09: remove one invigilator from S01, which needs two.")

# Make the plan of the small dataset.
code, output = run(PYTHON, "-B", "engine/main.py", SMALL_DATASET, "--output", work / "plans")
expect_code(code, 0)
plans = list((work / "plans").iterdir())
plan = plans[0]

# Delete T001's duty in S01 on 2 November morning from duties.csv.
duties = plan / "duties.csv"
expect_one_line("2026-11-02,morning,S01,T001", duties)
delete_line(duties, "2026-11-02,morning,S01,T001")

# Check the plan. Exit code 3 means a broken rule.
code, output = run(PYTHON, "-B", "engine/check.py", SMALL_DATASET, plan)
expect_code(code, 3)
expect_text(output, "Rule: teachers per room")
expect_text(output, "S01 on 2026-11-02 morning has 1 teacher(s) (T003)")

print("PASS: the checker found the room with too few teachers.")
