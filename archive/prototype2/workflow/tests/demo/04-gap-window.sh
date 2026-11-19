#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 04: Three papers cannot fit into 2-4 November with a two-day gap.\n'
expect_no_plan window_too_short gap
require_text 'at most 2 papers fit' "$report"
printf 'PASS: The planner explained the gap failure and wrote only why.txt.\n'
