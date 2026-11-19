# Start here: keyboard menu

This is the latest input-selection interface, replacing numbered entry for
normal use. Older files are intentionally untouched at Krish's request.
Read `../../repo_instructions.md`, this README, and PROGRESS before continuing.

Run `menu.py` in an interactive Windows terminal. It reuses
`../input_selection.py` for native pickers and path checks. Up/Down navigates;
Enter selects/replaces; success advances to the next missing input; Delete
clears only the highlighted choice and stays there; Cancel preserves progress.
Use the existing `prototype1/data/main` as read-only input. Do not use `demo`.

22 tests pass across the new and earlier suites. Real terminal navigation,
Delete and Exit were checked. Existing source/data/docs were hash-compared and
unchanged. No new dependency or dataset. New files only.

Exact next step: await Krish's visual review of select -> auto-advance -> move
back -> Delete, and picker Cancel. Do not start calendars or generation until
he has checked this step. Later agreed design: separate Tkinter calendars for
exam range and no-exam days, prefilled restrictions, remaining settings read
from the selected file. Original files must remain untouched.

Available interpreter:
`C:/Users/rs224/AppData/Roaming/uv/python/cpython-3.14-windows-x86_64-none/python.exe`.
Use `-B` to avoid creating bytecode files. No Git commands without explicit
instruction, and never push.
