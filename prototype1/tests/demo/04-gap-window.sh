#!/usr/bin/env bash
# Case 04: every student writes 3 papers, but the window is only 2 to 4
# November, and two papers of a student need a clear day between them.
# Expected: main.py says no plan is possible (exit code 2) under "Rule: gap",
# and writes only why.txt, holding the same text it printed.
source "$(dirname "$0")/setup.bash"
echo "Case 04: three papers can't fit into 2-4 November with a two-day gap."

# The impossible dataset: the small dataset with end_date 2026-11-04.
run "$PYTHON" -B main.py data/impossible/window_too_short --output "$work/no_plan"
expect_code 2
expect_text "at most 2 papers fit"

# One new folder, holding only why.txt: never half a plan.
folders=("$work"/no_plan/*)
files=("${folders[0]}"/*)
if [[ ${#folders[@]} != 1 || ${#files[@]} != 1 || ${files[0]} != *why.txt ]]; then
    fail "expected one folder holding only why.txt"
fi

# why.txt names the rule, and is what main.py printed.
why=$(tr -d '\r' < "${folders[0]}/why.txt")
if [[ $why != *"Rule: gap"* ]]; then
    fail "why.txt does not name Rule: gap"
fi
expect_text "$why"

echo "PASS: the planner explained the gap failure and wrote only why.txt."
