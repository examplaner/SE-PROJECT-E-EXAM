# The start every demo case shares. Each case loads it with `source`.

# Stop at the first command that fails, and treat an unset variable as an error.
set -euo pipefail

# Work from prototype1/, whatever folder the case was started from, so the
# cases can name main.py, check.py and data/ directly.
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

# The datasets the cases use.
# 16 students, 3 rooms, one week: small enough to check by hand.
small_dataset=data/tiny
# 1,600 students, 36 rooms, three weeks.
realistic_dataset=data/main

# The Python to run: $PYTHON if it is set, otherwise python, otherwise python3.
if [[ -z "${PYTHON:-}" ]]; then
    if command -v python >/dev/null 2>&1; then
        PYTHON=python
    else
        PYTHON=python3
    fi
fi

# A new empty folder for this case's plans and copied inputs.
# It is deleted when the case ends, whether it passes or fails.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# fail MESSAGE: say why the case failed and stop with exit code 1.
fail() {
    echo "FAIL: $1"
    exit 1
}

# run COMMAND...: run it and show what it printed. The printed text is kept
# in $output and the exit code in $code. Windows ends lines with \r\n, so the
# \r is removed to make the text checks work the same on every system.
run() {
    echo
    echo "\$ $*"
    code=0
    output=$("$@" 2>&1) || code=$?
    output=${output//$'\r'/}
    echo "$output"
    echo "Exit code: $code"
}

# expect_code EXPECTED: the last command run gave this exit code.
expect_code() {
    if [[ "$code" != "$1" ]]; then
        fail "exit code $code, expected $1"
    fi
}

# expect_text TEXT: the last command run printed this text.
expect_text() {
    if [[ "$output" != *"$1"* ]]; then
        fail "missing text: $1"
    fi
}

# expect_one_line TEXT FILE: exactly one line of the file holds the text, so
# the change a case makes to the file is the change it means to make.
expect_one_line() {
    if [[ $(grep -c -F -- "$1" "$2") != 1 ]]; then
        fail "expected '$1' on exactly one line of $2"
    fi
}
