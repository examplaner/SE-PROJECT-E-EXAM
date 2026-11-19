"""Case 06: the only room, S01, gives one paper 12 seats (every other seat
column), but paper CSE2001 has 16 students.
Expected: main.py says no plan is possible (exit code 2) under
"Rule: seats", and writes only why.txt, holding the same text it printed."""

from demo_helpers import PYTHON, expect_code, expect_text, fail, new_work_folder, run

work = new_work_folder()
print("Case 06: a paper with 16 students has only 12 seats it may use.")

# The impossible dataset: the small dataset with S01 as its only room.
code, output = run(PYTHON, "-B", "engine/main.py", "data/impossible/paper_too_big",
                   "--output", work / "no_plan")
expect_code(code, 2)
expect_text(output, "CSE2001 (16 students)")
expect_text(output, "12 seats to one paper")

# One new folder, holding only why.txt: never half a plan.
folders = list((work / "no_plan").iterdir())
files = list(folders[0].iterdir())
if len(folders) != 1 or len(files) != 1 or files[0].name != "why.txt":
    fail("expected one folder holding only why.txt")

# why.txt names the rule, and is what main.py printed.
why = files[0].read_text(encoding="utf-8").rstrip()
if "Rule: seats" not in why:
    fail("why.txt does not name Rule: seats")
expect_text(output, why)

print("PASS: the planner explained the seat shortage and wrote only why.txt.")
