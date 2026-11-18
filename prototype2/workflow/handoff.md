# Start here: full interactive workflow

Latest entry point is `prototype2/workflow/run.py`. Older entry points are left
unchanged because Krish forbids modifying existing files. Read repository rules
and this folder's README/PROGRESS before work. Do not use `demo`, alter original
data, overwrite outputs, or run Git commands without explicit instruction.

Run with the already installed `C:/Users/rs224/anaconda3/python.exe -B`.
The uv Python used for the early menu lacks PyYAML. No packages were installed.

Implemented: persistent arrow-menu input selections -> range calendar ->
no-exam calendar -> timetable Yes/No -> seating Yes/No. No returns to inputs.
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
the populated input menu, then generation paths and a short-range retry. Do not
start a new feature until he reviews this result. Tests do not substitute for
that human check. Selections persist within one run only, not after exiting.
