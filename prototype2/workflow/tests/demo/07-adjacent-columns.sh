#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 07: Move BT2CSE0007 from column 3 to column 2 in S01.\n'
build_plan "$data/tiny"
replace_once "$plan/daywise_seating_plans/2026-11-02/morning/S01.csv" \
    'CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007' \
    'CSE2001:BT2CSE0001,CSE2001:BT2CSE0007,'
check_plan 3 "$data/tiny"
require_text 'Rule: column rule' "$report"
require_text 'S01.csv, columns 1 and 2: CSE2001 sits in both' "$report"
printf 'PASS: The checker identified the adjacent columns and the paper.\n'
