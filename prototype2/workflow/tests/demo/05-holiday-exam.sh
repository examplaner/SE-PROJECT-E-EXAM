#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 05: Mark 4 November as a holiday after generating the plan.\n'
build_plan "$data/tiny"
cp -R "$data/tiny" "$output_dir/input"
replace_once "$output_dir/input/settings.yaml" 'holidays: []' 'holidays: [2026-11-04]'
check_plan 3 "$output_dir/input"
require_text 'Rule: exam days' "$report"
require_text 'CSE2002 is on 2026-11-04, a holiday' "$report"
printf 'PASS: The checker identified the paper scheduled on a holiday.\n'
