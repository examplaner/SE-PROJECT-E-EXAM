#!/usr/bin/env bash
# Case 05: after the plan is made, 4 November becomes a holiday.
# Expected: check.py, given the changed settings, finds the paper written on
# 4 November (exit code 3, "Rule: exam days").
source "$(dirname "$0")/setup.bash"
echo "Case 05: mark 4 November as a holiday after making the plan."

# Make the plan of the small dataset.
run "$PYTHON" -B engine/main.py "$small_dataset" --output "$work/plans"
expect_code 0
plans=("$work"/plans/*)
plan=${plans[0]}

# Copy the input and make 4 November a holiday in the copy's settings.
cp -R "$small_dataset" "$work/input"
settings="$work/input/settings.yaml"
expect_one_line "holidays: []" "$settings"
# sed writes the changed file under a new name, and mv puts it in place.
sed 's/holidays: \[\]/holidays: [2026-11-04]/' "$settings" > "$settings.new"
mv "$settings.new" "$settings"

# Check the plan against the changed input. Exit code 3 means a broken rule.
run "$PYTHON" -B engine/check.py "$work/input" "$plan"
expect_code 3
expect_text "Rule: exam days"
expect_text "CSE2002 is on 2026-11-04, a holiday"

echo "PASS: the checker found the paper written on a holiday."
