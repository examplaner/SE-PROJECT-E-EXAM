# Prototype 2 progress

## 2026-11-17 — input selection step

Approved scope: new files in `prototype2/` for terminal file/folder selection.
Krish chose Cancel returning to the previous selection menu, preserving earlier
choices, because he does not want to lose the whole progress.

Implemented `input_selection.py`: a numbered menu, individual CSV/YAML file
pickers, one student-list folder picker, replacement selections, Cancel/back,
path checks, and a completed-selection summary. Initial browsing location is
the existing `prototype1/data/main`; no data is selected automatically.

No pre-existing source, data, documentation, or progress files were edited.
No dataset was created or copied; `demo` is not used by the implementation.
No dependency installation, Git commands, commits, or pushes in this step.

Validation: 10 `unittest` tests pass using existing `main` inputs and mocked
dialogs. Terminal entry point also runs and exits correctly on `q`. Native
picker appearance and focus still require Krish's manual check. Tests use `-B`
so they do not write Python bytecode files.

Current environment: executable at
`C:/Users/rs224/AppData/Roaming/uv/python/cpython-3.14-windows-x86_64-none/python.exe`.
Tkinter imports successfully. This step needs neither PyYAML nor pytest;
both data-content validation and planner integration are later steps.

## Next gate

Krish opens the picker, selects `main/teachers.csv`, reopens Teachers and presses
Cancel. Confirm that the terminal menu still shows the earlier teacher choice.
Then try the student folder picker with `main/sections`. Wait for his feedback
before implementing another step.

## Decisions for later steps

- Tkinter calendars; separate exam-range and no-exam-day windows.
- Begin with restrictions from the selected settings; allow run-specific changes.
- Sessions, gap and invigilator count come from the settings file.
- Single files use a file picker, multiple-file inputs use a folder picker.
- Defer filename-policy changes; keep original data read-only.
- New implementation/output files only. Never overwrite an existing output.
- Still to design: passing the effective selections/settings into the planner
  and independent checker without changing the original input files.
