#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 10: Swap T003 and T005 while keeping both rooms fully staffed.\n'
build_plan "$data/tiny"
replace_once "$plan/duties.csv" '2026-11-02,morning,S01,T003' '2026-11-02,morning,S01,T005'
replace_once "$plan/duties.csv" '2026-11-02,morning,S02,T005' '2026-11-02,morning,S02,T003'
check_plan 3 "$data/tiny"
require_text 'Rule: own students' "$report"
require_text 'T003 is in S02 on 2026-11-02 morning, with their own students' "$report"
printf 'PASS: The checker detected a teacher supervising their own students.\n'
