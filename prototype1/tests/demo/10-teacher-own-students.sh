#!/usr/bin/env bash
# Case 10: teachers T003 and T005 swap rooms on 2 November morning. Both rooms
# still have two teachers, but T003 teaches the students now in front of them.
# Expected: check.py finds a teacher with their own students (exit code 3,
# "Rule: own students").
source "$(dirname "$0")/setup.bash"
echo "Case 10: swap T003 and T005, keeping both rooms fully staffed."

# Make the plan of the small dataset.
run "$PYTHON" -B main.py "$small_dataset" --output "$work/plans"
expect_code 0
plans=("$work"/plans/*)
plan=${plans[0]}

# T003 sits in S01 and T005 in S02. Swap them with one sed command: the
# first change rewrites T003's line, the second T005's. sed writes the
# changed file to a new file, and mv puts it in place.
duties="$plan/duties.csv"
expect_one_line "2026-11-02,morning,S01,T003" "$duties"
expect_one_line "2026-11-02,morning,S02,T005" "$duties"
sed -e 's/2026-11-02,morning,S01,T003/2026-11-02,morning,S01,T005/' \
    -e 's/2026-11-02,morning,S02,T005/2026-11-02,morning,S02,T003/' \
    "$duties" > "$duties.new"
mv "$duties.new" "$duties"

# Check the plan. Exit code 3 means a broken rule.
run "$PYTHON" -B check.py "$small_dataset" "$plan"
expect_code 3
expect_text "Rule: own students"
expect_text "T003 is in S02 on 2026-11-02 morning, with their own students"

echo "PASS: the checker found a teacher supervising their own students."
