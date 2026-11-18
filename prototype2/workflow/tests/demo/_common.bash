# Shared setup and assertions for the standalone demo scripts.
set -euo pipefail

demo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
workflow_dir="$(cd -- "$demo_dir/../.." && pwd)"
engine="$workflow_dir/engine"
data="$(cd -- "$workflow_dir/../../prototype1/data" && pwd)"
output_dir="$(mktemp -d)"
trap 'rm -rf -- "$output_dir"' EXIT

if [[ -z "${PYTHON:-}" ]]; then
    if command -v python >/dev/null 2>&1; then
        PYTHON=python
    else
        PYTHON=python3
    fi
fi

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

require_text() {
    local expected="$1" actual="$2"
    [[ "$actual" == *"$expected"* ]] || fail "Missing expected text: $expected"
}

run_expect() {
    local expected="$1" status=0
    shift
    printf '\n$'
    printf ' %q' "$@"
    printf '\n'
    report=$("$@" 2>&1) || status=$?
    report=${report//$'\r'/}
    printf '%s\nExit code: %s (expected %s)\n' "$report" "$status" "$expected"
    [[ "$status" -eq "$expected" ]] || fail "Unexpected exit code"
}

build_plan() {
    run_expect 0 "$PYTHON" -B "$engine/main.py" "$1" --output "$output_dir/plans"
    local folders=("$output_dir/plans/"*/)
    [[ ${#folders[@]} -eq 1 && -f "${folders[0]}schedule.csv" ]] ||
        fail "Expected one generated plan"
    plan="${folders[0]%/}"
}

check_plan() {
    run_expect "$1" "$PYTHON" -B "$engine/check.py" "$2" "$plan"
}

expect_no_plan() {
    run_expect 2 "$PYTHON" -B "$engine/main.py" "$data/impossible/$1" --output "$output_dir/no-plan"
    local folders=("$output_dir/no-plan/"*/)
    [[ ${#folders[@]} -eq 1 && -f "${folders[0]}why.txt" ]] ||
        fail "Expected one failure folder containing why.txt"
    local entries=("${folders[0]}"*)
    [[ ${#entries[@]} -eq 1 ]] || fail "Unexpected files beside why.txt"
    local reason
    reason=$(<"${folders[0]}why.txt")
    reason=${reason//$'\r'/}
    require_text "Rule: $2" "$reason"
    require_text "$reason" "$report"
}

replace_once() {
    "$PYTHON" -B - "$@" <<'PYTHON_SCRIPT'
from pathlib import Path
import sys

filename, old, new = sys.argv[1:]
path = Path(filename)
with path.open(encoding="utf-8", newline="") as stream:
    original = stream.read()
if "\r\n" in original:
    old = old.replace("\n", "\r\n")
    new = new.replace("\n", "\r\n")
if original.count(old) != 1:
    sys.exit(f"FAIL: Expected one match for {old!r} in {path.name}.")
with path.open("w", encoding="utf-8", newline="") as stream:
    stream.write(original.replace(old, new, 1))
PYTHON_SCRIPT
}
