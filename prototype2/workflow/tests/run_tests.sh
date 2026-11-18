#!/usr/bin/env bash
set -eu

usage() {
    printf 'Usage: bash "%s" [demo|impossible|validation|schedule|seating|duties|no-plan|checker|workflow|all|--all]\n' "$0"
}

if (( $# > 1 )); then
    usage >&2
    exit 2
fi
group=${1-demo}
case "$group" in
    -h|--help) usage; exit 0 ;;
    demo|impossible|validation|schedule|seating|duties|no-plan|checker|workflow|all|--all) ;;
    *) usage >&2; exit 2 ;;
esac

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
if [[ -x "$HOME/anaconda3/python.exe" ]]; then
    python="$HOME/anaconda3/python.exe"
elif command -v python >/dev/null; then
    python=python
else
    python=python3
fi

suite() {
    "$python" -B -m pytest -p no:cacheprovider -v --tb=short "$@"
}

case "$group" in
    demo|impossible) "$python" -B prototype2/workflow/tests/show_cases.py "$group" ;;
    validation)
        suite prototype1/tests/test_validate.py
        suite prototype2/workflow/tests/test_live_validation.py
        ;;
    schedule) suite prototype1/tests/test_schedule.py ;;
    seating) suite prototype1/tests/test_seat.py ;;
    duties) suite prototype1/tests/test_duties.py ;;
    no-plan) suite prototype1/tests/test_no_plan.py ;;
    checker) suite prototype1/tests/test_check.py ;;
    workflow) suite prototype2/workflow/tests ;;
    all|--all)
        # The prototypes use some of the same module names. Start each suite fresh.
        suite prototype1/tests
        suite prototype2/tests
        suite prototype2/keyboard_cli/tests
        suite prototype2/workflow/tests
        echo "PASS - all four test suites passed."
        ;;
esac
