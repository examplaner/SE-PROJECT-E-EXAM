#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 08: Remove the seat for registered student BT2CSE0006.\n'
build_plan "$data/tiny"
replace_once "$plan/daywise_seating_plans/2026-11-02/morning/S01.csv" \
    'CSE2001:BT2CSE0006' ''
check_plan 3 "$data/tiny"
require_text 'Rule: seated once' "$report"
require_text 'no seat for 1 registered student(s): BT2CSE0006' "$report"
printf 'PASS: The checker identified the missing student seat.\n'
