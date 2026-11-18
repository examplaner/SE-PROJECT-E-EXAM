#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 09: Remove one invigilator from S01, which requires two.\n'
build_plan "$data/tiny"
replace_once "$plan/duties.csv" $'2026-11-02,morning,S01,T001\n' ''
check_plan 3 "$data/tiny"
require_text 'Rule: teachers per room' "$report"
require_text 'S01 on 2026-11-02 morning has 1 teacher(s) (T003)' "$report"
printf 'PASS: The checker identified the room with too few teachers.\n'
