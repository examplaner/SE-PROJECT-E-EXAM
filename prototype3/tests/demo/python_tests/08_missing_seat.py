"""Case 08: the seat of registered student BT2CSE0006 is emptied.
Expected: check.py finds a student with no seat (exit code 3,
"Rule: seated once") and names the student."""

from demo_helpers import (PYTHON, SMALL_DATASET, expect_code, expect_one_line, expect_text,
                          new_work_folder, replace_in_file, run)

work = new_work_folder()
print("Case 08: remove the seat of registered student BT2CSE0006.")

# Make the plan of the small dataset.
code, output = run(PYTHON, "-B", "engine/main.py", SMALL_DATASET, "--output", work / "plans")
expect_code(code, 0)
plans = list((work / "plans").iterdir())
plan = plans[0]

# Empty BT2CSE0006's seat in S01 on 2 November morning.
room = plan / "daywise_seating_plans" / "2026-11-02" / "morning" / "S01.csv"
expect_one_line("CSE2001:BT2CSE0006", room)
replace_in_file(room, "CSE2001:BT2CSE0006", "")

# Check the plan. Exit code 3 means a broken rule.
code, output = run(PYTHON, "-B", "engine/check.py", SMALL_DATASET, plan)
expect_code(code, 3)
expect_text(output, "Rule: seated once")
expect_text(output, "no seat for 1 registered student(s): BT2CSE0006")

print("PASS: the checker found the student with no seat.")
