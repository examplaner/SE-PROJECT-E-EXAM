#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/_common.bash"

printf 'Case 03: CSE2001 and CSE2003 share one question paper.\n'
build_plan "$data/tiny"
"$PYTHON" -B - "$plan/schedule.csv" <<'PYTHON_SCRIPT'
import csv
import sys

with open(sys.argv[1], newline="", encoding="utf-8") as stream:
    rows = list(csv.DictReader(stream))

codes = {"CSE2001", "CSE2003"}
matches = [row for row in rows if codes.intersection(row["course_codes"].split(";"))]
if not (len(rows) == 7 and len(matches) == 1
        and set(matches[0]["course_codes"].split(";")) == codes):
    sys.exit("FAIL: Expected seven papers and exactly one shared row for CSE2001 and CSE2003.")
print("Shared timetable row:", matches[0])
PYTHON_SCRIPT
printf 'PASS: Both course codes appear in exactly one paper row.\n'
