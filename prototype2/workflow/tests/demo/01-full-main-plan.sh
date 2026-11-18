#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 01: Generate the full main dataset and check all outputs.\n'
build_plan "$data/main"
check_plan 0 "$data/main"
require_text 'no problems' "$report"
require_text '56 papers, 454 room files, 8750 seats, 908 duties' "$report"
printf 'PASS: The full plan passed the checker with the expected totals.\n'
