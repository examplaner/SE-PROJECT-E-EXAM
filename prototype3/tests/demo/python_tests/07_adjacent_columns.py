"""Case 07: in room S01, student BT2CSE0007 moves from seat column 3 to
column 2, right next to the same paper in column 1.
Expected: check.py finds the broken column rule (exit code 3) and names
the room, the columns and the paper."""

from demo_helpers import (PYTHON, SMALL_DATASET, expect_code, expect_one_line, expect_text,
                          new_work_folder, replace_in_file, run)

work = new_work_folder()
print("Case 07: move BT2CSE0007 from column 3 to column 2 in S01.")

# Make the plan of the small dataset.
code, output = run(PYTHON, "-B", "engine/main.py", SMALL_DATASET, "--output", work / "plans")
expect_code(code, 0)
plans = list((work / "plans").iterdir())
plan = plans[0]

# S01 on 2 November morning. Its first row of seats reads
# "CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007": column 2 is empty.
room = plan / "daywise_seating_plans" / "2026-11-02" / "morning" / "S01.csv"
expect_one_line("CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007", room)
# Move BT2CSE0007 into column 2.
replace_in_file(room, "CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007",
                "CSE2001:BT2CSE0001,CSE2001:BT2CSE0007,")

# Check the plan. Exit code 3 means a broken rule.
code, output = run(PYTHON, "-B", "engine/check.py", SMALL_DATASET, plan)
expect_code(code, 3)
expect_text(output, "Rule: column rule")
expect_text(output, "S01.csv, columns 1 and 2: CSE2001 sits in both")

print("PASS: the checker found the paper in neighbouring columns.")
