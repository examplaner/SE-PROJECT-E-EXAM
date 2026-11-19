"""Case 04: every student writes 3 papers, but the window is only 2 to 4
November, and two papers of a student need a clear day between them.
Expected: main.py says no plan is possible (exit code 2) under "Rule: gap",
and writes only why.txt, holding the same text it printed."""

from demo_helpers import PYTHON, expect_code, expect_text, fail, new_work_folder, run

work = new_work_folder()
print("Case 04: three papers can't fit into 2-4 November with a two-day gap.")

# The impossible dataset: the small dataset with end_date 2026-11-04.
code, output = run(PYTHON, "-B", "engine/main.py", "data/impossible/window_too_short",
                   "--output", work / "no_plan")
expect_code(code, 2)
expect_text(output, "at most 2 papers fit")

# One new folder, holding only why.txt: never half a plan.
folders = list((work / "no_plan").iterdir())
files = list(folders[0].iterdir())
if len(folders) != 1 or len(files) != 1 or files[0].name != "why.txt":
    fail("expected one folder holding only why.txt")

# why.txt names the rule, and is what main.py printed.
why = files[0].read_text(encoding="utf-8").rstrip()
if "Rule: gap" not in why:
    fail("why.txt does not name Rule: gap")
expect_text(output, why)

print("PASS: the planner explained the gap failure and wrote only why.txt.")
