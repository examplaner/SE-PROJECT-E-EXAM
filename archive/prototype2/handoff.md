# Start here

Read `../repo_instructions.md`, this prototype's README, and PROGRESS first.

The current approved step is implemented: `input_selection.py` provides a
terminal menu with native file/folder pickers. Cancel returns to the menu and
preserves earlier choices. Students use one folder picker; the other inputs
use single-file pickers. Use existing `prototype1/data/main` as read-only input.
Do not use `demo`. Do not modify pre-existing files or generate new datasets.

10 tests pass (`python -B -m unittest discover -s prototype2/tests -v` from the
repository root). The terminal entry point was checked with `q`; native dialogs
were mocked in tests and still need a human visual check. No packages installed.
Python available here:
`C:/Users/rs224/AppData/Roaming/uv/python/cpython-3.14-windows-x86_64-none/python.exe`.

Exact next step: wait for Krish to run the menu, choose `main/teachers.csv`,
reopen that picker, cancel, and confirm the earlier selection remains. Do not
start calendar or engine work until he reviews this result.

Later scope: separate Tkinter calendars for date range and excluded days;
preselect existing restrictions; sessions, gap and invigilator count from the
settings file. Input selections are currently in memory only. No plan generation
or data-content validation is connected yet. No commits or pushes.
