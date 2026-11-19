#!/usr/bin/env bash
# Case 03: CSE2001 and CSE2003 are one question paper written by two cohorts
# (constraints.yaml, same_paper).
# Expected: the date sheet has 7 papers, and exactly one row holds both codes.
source "$(dirname "$0")/setup.bash"
echo "Case 03: CSE2001 and CSE2003 share one question paper."

# Make the plan of the small dataset.
run "$PYTHON" -B engine/main.py "$small_dataset" --output "$work/plans"
expect_code 0
plans=("$work"/plans/*)
schedule="${plans[0]}/schedule.csv"

# The date sheet has a header line and one line per paper: 8 lines, 7 papers.
# (( )) compares numbers, so the spaces Mac's wc puts before the count don't matter.
lines=$(wc -l < "$schedule")
if (( lines != 8 )); then
    fail "expected 7 papers in schedule.csv, found $((lines - 1))"
fi

# Only one line names either code: the shared paper is written once.
if [[ $(grep -c -E "CSE2001|CSE2003" "$schedule") != 1 ]]; then
    fail "expected exactly one row for CSE2001 and CSE2003"
fi

# Its course_codes column (the 4th) lists both codes, joined with ';'.
row=$(grep -E "CSE2001|CSE2003" "$schedule" | tr -d '\r')
echo "Shared row: $row"
codes=$(echo "$row" | cut -d, -f4)
if [[ $codes != "CSE2001;CSE2003" ]]; then
    fail "the shared row lists $codes, expected CSE2001;CSE2003"
fi

echo "PASS: both course codes are in one paper row."
