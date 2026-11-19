# Interactive exam planning

Krish's requested workflow: select inputs, choose the exam range and no-exam
days in separate calendars, then ask before generating the timetable and before
writing the seating plan. No returns to selection without losing progress.
If scheduling fails, reuse the existing explanation and terms guide, and allow
the exam range to be extended without selecting all files again.

This is a new entry point. All previous files remain unchanged. The `engine/`
folder contains an unchanged copy of prototype1's planning and checking source
and terms guide; no input datasets are copied or generated.

On Windows, open an interactive PowerShell terminal in the repository folder.
Use Python 3.10 or newer with Tkinter and venv. Git for Windows supplies Bash
for the demo tests. The setup command downloads the Python dependencies into
the workflow's local virtual environment.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\prototype2\workflow\setup.ps1 -Verify -Launch
```

`-Verify` runs the engine tests, workflow tests, and all ten Bash demo cases.
`-Launch` starts the interactive workflow after setup. To launch again without
running setup, use:

```powershell
& .\prototype2\workflow\.venv\Scripts\python.exe -B .\prototype2\workflow\run.py
```

To present one case at a time, open Git Bash in the repository folder:

```bash
export PYTHON="$PWD/prototype2/workflow/.venv/Scripts/python.exe"
bash prototype2/workflow/tests/demo/04-gap-window.sh
```

Up/Down and Enter navigate terminal choices. Delete clears an input choice,
never its file. File/folder picker Cancel preserves that choice. Calendar Back
or closing its window returns to the previous step and retains confirmed dates.
Selections remain in memory while the program is running, not across restarts.

Inputs start browsing in `prototype1/data/main`. Select `sections.csv` for section
information and the `sections` folder for student lists. Students retain the
existing section filenames. Other selected filenames may differ. Sessions,
minimum gap and invigilators per room come from the selected settings file.
Choose start and end dates in the first calendar. In the second calendar, click
dates to mark/unmark exclusions. Existing weekday and holiday restrictions are
preselected; added range dates inherit the file's restrictions. Back preserves
confirmed choices. No source settings file is written.

Choose Yes to generate the timetable. No returns to input selection. The engine
checks seating and teacher feasibility before publishing a timetable, but the
seating files are written only after the second Yes. The timetable and complete
seating/duty plan are checked using the existing independent checker rules.
Every attempt uses a fresh folder under `prototype2/output`; the terminal shows
absolute output paths. Existing outputs are never overwritten. Run settings
and source paths/hashes are recorded beside the outputs, not as a new dataset.

Failures retain the engine's original reason in a fresh `why.txt`. The terminal
also shows the existing terms guide path. Gap/no-exam-day failures return to the
range calendar after the explanation. Other failures offer date/input recovery.
No input selections are lost. Adjusting inputs invalidates the in-memory plan;
previously saved outputs remain untouched.

## Testing and review

Tests are in `tests/` and use existing `main` and existing impossible cases.
Run with `python -B -m unittest discover -s prototype2/workflow/tests -v`.
Native calendar/picker interaction also needs a human visual review.

Read `PROGRESS.md` and `handoff.md` for this step's verification and next check.
