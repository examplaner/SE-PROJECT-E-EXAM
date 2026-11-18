#!/usr/bin/env bash
# Case 07: in room S01, student BT2CSE0007 moves from seat column 3 to
# column 2, right next to the same paper in column 1.
# Expected: check.py finds the broken column rule (exit code 3) and names
# the room, the columns and the paper.
source "$(dirname "$0")/setup.bash"
echo "Case 07: move BT2CSE0007 from column 3 to column 2 in S01."

# Make the plan of the small dataset.
run "$PYTHON" -B main.py "$small_dataset" --output "$work/plans"
expect_code 0
plans=("$work"/plans/*)
plan=${plans[0]}

# S01 on 2 November morning. Its first row of seats reads
# "CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007": column 2 is empty.
room="$plan/daywise_seating_plans/2026-11-02/morning/S01.csv"
expect_one_line "CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007" "$room"
# Move BT2CSE0007 into column 2. sed writes the changed room to a new file,
# and mv puts it in place.
sed 's/CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007/CSE2001:BT2CSE0001,CSE2001:BT2CSE0007,/' \
    "$room" > "$room.new"
mv "$room.new" "$room"

# Check the plan. Exit code 3 means a broken rule.
run "$PYTHON" -B check.py "$small_dataset" "$plan"
expect_code 3
expect_text "Rule: column rule"
expect_text "S01.csv, columns 1 and 2: CSE2001 sits in both"

echo "PASS: the checker found the paper in neighbouring columns."
