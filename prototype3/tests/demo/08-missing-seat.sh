#!/usr/bin/env bash
# Case 08: the seat of registered student BT2CSE0006 is emptied.
# Expected: check.py finds a student with no seat (exit code 3,
# "Rule: seated once") and names the student.
source "$(dirname "$0")/setup.bash"
echo "Case 08: remove the seat of registered student BT2CSE0006."

# Make the plan of the small dataset.
run "$PYTHON" -B engine/main.py "$small_dataset" --output "$work/plans"
expect_code 0
plans=("$work"/plans/*)
plan=${plans[0]}

# Empty BT2CSE0006's seat in S01 on 2 November morning. sed writes the
# changed room to a new file, and mv puts it in place.
room="$plan/daywise_seating_plans/2026-11-02/morning/S01.csv"
expect_one_line "CSE2001:BT2CSE0006" "$room"
sed 's/CSE2001:BT2CSE0006//' "$room" > "$room.new"
mv "$room.new" "$room"

# Check the plan. Exit code 3 means a broken rule.
run "$PYTHON" -B engine/check.py "$small_dataset" "$plan"
expect_code 3
expect_text "Rule: seated once"
expect_text "no seat for 1 registered student(s): BT2CSE0006"

echo "PASS: the checker found the student with no seat."
