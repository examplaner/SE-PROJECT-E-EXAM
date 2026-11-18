#!/usr/bin/env bash
# Case 02: a student is registered for a course that does not exist.
# Expected: main.py stops with exit code 1, names the file, the row and the
# unknown course code, and writes no output folder.
source "$(dirname "$0")/setup.bash"
echo "Case 02: add a registration for a course that does not exist."

# Copy the small dataset, so the real one stays untouched.
cp -R "$small_dataset" "$work/input"

# Register student BT2CSE0001 for CSE9999, which is not in courses.csv.
echo "BT2CSE0001,CSE9999" >> "$work/input/registrations.csv"

# Try to make a plan. Exit code 1 means the input is invalid.
run "$PYTHON" -B main.py "$work/input" --output "$work/plans"
expect_code 1
expect_text "registrations.csv row"
expect_text "course code CSE9999 is not in courses.csv"

# Invalid input never gets an output folder.
if [[ -e "$work/plans" ]]; then
    fail "invalid input created an output folder"
fi

echo "PASS: the input check found the bad registration."
