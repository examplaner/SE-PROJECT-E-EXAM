# Start here: full interactive workflow

Next review: run `examplan` with the `waiting_paper` dataset from
`prototype1/data/impossible`. Keep its calendar settings and generate the
timetable. Check that the terminal shows `Rule: duty room`, the `why.txt`
path, and when `basis.txt` is created. Successful saves print the `basis.txt`
path for each output.

For the classroom demonstration, open Git Bash in the repository and run
`bash prototype2/workflow/tests/run_tests.sh`. Next run it with `impossible`
to show the seven engine failure reasons. The Git Bash section of
`TEST_CASES.md` lists the other groups.

For the teacher's test review, open **Show both stages live in examplan**
in `TEST_CASES.md`. The CLI checks file structure and available data rules
during selection and checks the complete selection again before the calendars.
Next, demonstrate a wrong header in Teachers, then pick the ready-made
`prototype1/data/impossible/registrations_unknown_course.csv` before Courses,
observe row 50 and replace the file.

On this Windows account, open a new terminal in any folder and type `examplan`.
The launcher uses the existing Anaconda installation and this checkout's
`run.py`. The command was verified outside the repository on 2026-11-18.

Latest entry point is `prototype2/workflow/run.py`. Older entry points are left
unchanged because Krish forbids modifying existing files. Read repository rules
and this folder's README/PROGRESS before work. Do not use `demo`, alter original
data, overwrite outputs, or run Git commands without explicit instruction.

Run with the already installed `C:/Users/rs224/anaconda3/python.exe -B`.
The uv Python used for the early menu lacks PyYAML. No packages were installed.

Implemented: persistent arrow-menu input selections -> range calendar ->
no-exam calendar -> timetable Yes/No -> seating and teacher duties Yes/No. No returns to inputs.
Cancellation/back keeps selections. Session names/gap/invigilator count come
from the selected settings file. Calendar edits stay in memory; effective
settings are saved beside output, never written back to the source.

The engine source and terms guide were copied unchanged into `engine/` to honor
prototype isolation. Failures use original NoPlan reasons/why.txt and a terms
path. Date/gap failures return to the range calendar. Other failures offer
calendar/input recovery. Full feasibility runs before the timetable is written;
seating/duty output waits for the second Yes. Every output gets a new directory.

16 tests pass, including real main generation (56 papers, 454 room files, 908
duties) checked independently. Tk controls exercised and previews reviewed.
Interactive terminal launcher checked. All original files left unchanged.

Exact next step: await Krish's visual review of calendars and No returning to
the populated input menu, then the seating folder and duties.csv paths shown
after the second Yes, and a short-range retry. Do not
start a new feature until he reviews this result. Tests do not substitute for
that human check. Selections persist within one run only, not after exiting.
