#!/usr/bin/env bash
# Case 09: one of the two invigilators of room S01 is taken off duty.
# Expected: check.py finds a room with too few teachers (exit code 3,
# "Rule: teachers per room") and names the room and who is left.
source "$(dirname "$0")/setup.bash"
echo "Case 09: remove one invigilator from S01, which needs two."

# Make the plan of the small dataset.
run "$PYTHON" -B main.py "$small_dataset" --output "$work/plans"
expect_code 0
plans=("$work"/plans/*)
plan=${plans[0]}

# Delete T001's duty in S01 on 2 November morning from duties.csv. sed
# writes the file without that line to a new file, and mv puts it in place.
duties="$plan/duties.csv"
expect_one_line "2026-11-02,morning,S01,T001" "$duties"
sed '/^2026-11-02,morning,S01,T001/d' "$duties" > "$duties.new"
mv "$duties.new" "$duties"

# Check the plan. Exit code 3 means a broken rule.
run "$PYTHON" -B check.py "$small_dataset" "$plan"
expect_code 3
expect_text "Rule: teachers per room"
expect_text "S01 on 2026-11-02 morning has 1 teacher(s) (T003)"

echo "PASS: the checker found the room with too few teachers."
