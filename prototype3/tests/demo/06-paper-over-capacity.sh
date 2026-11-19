#!/usr/bin/env bash
# Case 06: the only room, S01, gives one paper 12 seats (every other seat
# column), but paper CSE2001 has 16 students.
# Expected: main.py says no plan is possible (exit code 2) under
# "Rule: seats", and writes only why.txt, holding the same text it printed.
source "$(dirname "$0")/setup.bash"
echo "Case 06: a paper with 16 students has only 12 seats it may use."

# The impossible dataset: the small dataset with S01 as its only room.
run "$PYTHON" -B engine/main.py data/impossible/paper_too_big --output "$work/no_plan"
expect_code 2
expect_text "CSE2001 (16 students)"
expect_text "12 seats to one paper"

# One new folder, holding only why.txt: never half a plan.
folders=("$work"/no_plan/*)
files=("${folders[0]}"/*)
if [[ ${#folders[@]} != 1 || ${#files[@]} != 1 || ${files[0]} != *why.txt ]]; then
    fail "expected one folder holding only why.txt"
fi

# why.txt names the rule, and is what main.py printed.
why=$(tr -d '\r' < "${folders[0]}/why.txt")
if [[ $why != *"Rule: seats"* ]]; then
    fail "why.txt does not name Rule: seats"
fi
expect_text "$why"

echo "PASS: the planner explained the seat shortage and wrote only why.txt."
