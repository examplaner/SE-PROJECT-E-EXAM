# Invalid input files

Files broken on purpose, to show the input checks. Unlike `data/impossible/`, these are not whole datasets: each
one stands in for one file of `data/tiny`.

| File | What is wrong | What the checks say |
|---|---|---|
| `registrations_unknown_course.csv` | `data/tiny/registrations.csv` with one more row: `BT2CSE0001,CSE9999`. CSE9999 is not a course. | `registrations_unknown_course.csv row 50: course code CSE9999 is not in courses.csv` |

**In the app** (`python app.py`): choose every input from `data/tiny`, but this file for "Student course
registrations". The file on its own passes, because its header and rows are fine. "Continue to exam dates" then
runs the checks across files and shows row 50. Choose `data/tiny/registrations.csv` instead, and Continue works.

**On the command line**, the same check gives exit code 1: see demo case 02 in `tests/demo/`.

`python tests/app_checks.py` shows these steps, and a wrong header, without a person.
