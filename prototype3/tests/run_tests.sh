#!/usr/bin/env bash
# Run one group of tests, to show one part of the planner in class:
#
#   bash tests/run_tests.sh [group]
#
# app-checks (the default) shows the app's input checks; impossible runs the
# seven impossible datasets; every other group runs the unit tests of one part.
# run_tests.py does the same in Python.

# Stop at the first command that fails, and treat an unset variable as an error.
set -eu

# Work from prototype3/, whatever folder this was started from.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# The Python to run: $PYTHON if it is set, otherwise python, otherwise python3.
# On Windows, set PYTHON if "python" opens the Microsoft Store.
if [[ -z "${PYTHON:-}" ]]; then
    if command -v python >/dev/null 2>&1; then
        PYTHON=python
    else
        PYTHON=python3
    fi
fi

usage() {
    echo "Usage: bash tests/run_tests.sh [group]"
    echo "Groups: app-checks (default), impossible, validation, schedule, seating, duties,"
    echo "        no-plan, checker, app, all"
}

# suite FILE...: the unit tests in these files, one line per test. -B and
# no:cacheprovider keep the repo free of .pyc files and pytest's cache.
suite() {
    "$PYTHON" -B -m pytest -p no:cacheprovider -v --tb=short "$@"
}

# Each impossible dataset and the rule its reason must name, as folder:rule.
impossible_cases="no_exam_days:exam days
window_too_short:gap
paper_too_big:seats
no_day_fits:paper placement
waiting_paper:duty room
duty_room_full:duty room
too_few_teachers:duties"

# impossible: plan each impossible dataset. Each must exit with 2, write a
# folder holding only why.txt, name its rule there, and print the same text.
impossible() {
    work=$(mktemp -d)
    trap 'rm -rf "$work"' EXIT
    passed=0
    total=0
    while IFS=: read -r dataset rule; do
        total=$((total + 1))
        echo
        echo "$dataset (expected: exit 2, Rule: $rule, only why.txt)"
        code=0
        # "|| code=$?" keeps the exit code, and stops set -e from ending the run
        # < /dev/null, so the planner can't read the list this loop reads
        output=$("$PYTHON" -B engine/main.py "data/impossible/$dataset" --output "$work/$dataset" \
                 < /dev/null 2>&1) || code=$?
        # Windows ends lines with \r\n; the \r is removed so the text compares the same
        output=${output//$'\r'/}
        echo "$output"
        files=("$work/$dataset"/*/*)
        why=""
        if [[ ${#files[@]} == 1 && ${files[0]} == */why.txt ]]; then
            why=$(tr -d '\r' < "${files[0]}")
        fi
        if [[ $code == 2 && -n $why && $why == *"Rule: $rule"* && $output == *"$why"* ]]; then
            echo "PASS"
            passed=$((passed + 1))
        else
            echo "FAIL (exit code $code)"
        fi
    done <<< "$impossible_cases"
    echo
    echo "$passed/$total impossible datasets passed."
    [[ $passed == "$total" ]]
}

# One group at most; app-checks when none is given.
if (( $# > 1 )); then
    usage
    exit 2
fi
group=${1:-app-checks}
case "$group" in
    app-checks) "$PYTHON" -B tests/app_checks.py ;;
    impossible) impossible ;;
    validation) suite tests/unit/test_validate.py tests/unit/test_live_checks.py ;;
    schedule) suite tests/unit/test_schedule.py ;;
    seating) suite tests/unit/test_seat.py ;;
    duties) suite tests/unit/test_duties.py ;;
    no-plan) suite tests/unit/test_no_plan.py ;;
    checker) suite tests/unit/test_check.py ;;
    app) suite tests/unit/test_flow.py tests/unit/test_inputs.py tests/unit/test_calendars.py \
               tests/unit/test_planner.py tests/unit/test_live_checks.py ;;
    all) suite tests/unit ;;
    -h|--help) usage ;;
    *) usage; exit 2 ;;
esac
