#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 06: A paper with 16 students has only 12 legal seats.\n'
expect_no_plan paper_too_big seats
require_text 'CSE2001 (16 students)' "$report"
require_text '12 seats to one paper' "$report"
printf 'PASS: The planner explained the capacity failure and wrote only why.txt.\n'
