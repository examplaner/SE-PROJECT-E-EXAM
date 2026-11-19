"""Case 10: teachers T003 and T005 swap rooms on 2 November morning. Both rooms
still have two teachers, but T003 teaches the students now in front of them.
Expected: check.py finds a teacher with their own students (exit code 3,
"Rule: own students")."""

from demo_helpers import (PYTHON, SMALL_DATASET, expect_code, expect_one_line, expect_text,
                          new_work_folder, replace_in_file, run)

work = new_work_folder()
print("Case 10: swap T003 and T005, keeping both rooms fully staffed.")

# Make the plan of the small dataset.
code, output = run(PYTHON, "-B", "engine/main.py", SMALL_DATASET, "--output", work / "plans")
expect_code(code, 0)
plans = list((work / "plans").iterdir())
plan = plans[0]

# T003 sits in S01 and T005 in S02. Swap them: the first change rewrites
# T003's line, the second T005's.
duties = plan / "duties.csv"
expect_one_line("2026-11-02,morning,S01,T003", duties)
expect_one_line("2026-11-02,morning,S02,T005", duties)
replace_in_file(duties, "2026-11-02,morning,S01,T003", "2026-11-02,morning,S01,T005")
replace_in_file(duties, "2026-11-02,morning,S02,T005", "2026-11-02,morning,S02,T003")

# Check the plan. Exit code 3 means a broken rule.
code, output = run(PYTHON, "-B", "engine/check.py", SMALL_DATASET, plan)
expect_code(code, 3)
expect_text(output, "Rule: own students")
expect_text(output, "T003 is in S02 on 2026-11-02 morning, with their own students")

print("PASS: the checker found a teacher supervising their own students.")
