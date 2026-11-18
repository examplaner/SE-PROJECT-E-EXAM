#!/usr/bin/env bash
# Case 01: make the full plan of the realistic dataset and check all of it.
# Expected: main.py writes one plan folder, and check.py finds no problem in
# 56 papers, 454 room files, 8,750 seats and 908 duties.
source "$(dirname "$0")/setup.bash"
echo "Case 01: make the full plan of the realistic dataset and check all of it."

# Make the plan. Exit code 0 means a plan was written.
run "$PYTHON" -B main.py "$realistic_dataset" --output "$work/plans"
expect_code 0

# main.py made one new folder, and it holds the date sheet.
plans=("$work"/plans/*)
plan=${plans[0]}
if [[ ${#plans[@]} != 1 || ! -f "$plan/schedule.csv" ]]; then
    fail "expected one plan folder with schedule.csv"
fi

# Check the plan against the same input. Exit code 0 means no rule is broken.
run "$PYTHON" -B check.py "$realistic_dataset" "$plan"
expect_code 0
expect_text "no problems"
expect_text "56 papers, 454 room files, 8750 seats, 908 duties"

echo "PASS: the full plan passed the checker with the expected totals."
