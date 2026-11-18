#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 02: Add a registration for a course that does not exist.\n'
cp -R "$data/tiny" "$output_dir/input"
printf 'BT2CSE0001,CSE9999\n' >> "$output_dir/input/registrations.csv"
run_expect 1 "$PYTHON" -B "$engine/main.py" "$output_dir/input" --output "$output_dir/plans"
require_text 'registrations.csv row' "$report"
require_text 'course code CSE9999 is not in courses.csv' "$report"
[[ ! -e "$output_dir/plans" ]] || fail "Invalid input created an output folder"
printf 'PASS: Input validation identified the bad registration.\n'
