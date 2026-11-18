# Terminal controls for the exam planner

## Purpose, from Krish's request

> I want to work on the terminal-based control.
> A person should not have to put the path of the file.
> For those where we have multiple files we will go for the folder for now,
> and for the single file we will go for the file.

Cancel returns to the input menu and keeps the selections already made.
Krish's reason: "I don't want to lose the whole progress."

## Current step: select inputs

From the repository folder:

```powershell
python -B prototype2/input_selection.py
```

Choose a numbered input in the terminal. A file picker opens for a single
CSV or YAML file; a folder picker opens for all student-section CSVs.
The pickers initially browse `prototype1/data/main`. No input is selected
automatically. Select the `sections` folder for the student lists and
`sections.csv` for the section information.

The program remembers each choice while it runs. You can revisit any input
to replace it. Cancel closes the picker and returns to the menu without
changing any previous choice. Enter `done` to review the complete selection,
or `q` to leave the program. Choices are kept in memory, not saved between runs.

This step checks that selected paths exist, file extensions match, files can
be opened, and the student folder has CSV files. It does not yet validate
CSV columns or relationships, open calendars, or generate an exam plan.
No source file is written, renamed, or copied. `demo` is not used.

Tkinter is Python's standard interface for desktop windows; its file-dialog
functions provide the file and folder pickers. No third-party package is
needed for this step. Some Python distributions omit Tkinter; the program
reports that problem without losing current choices.

## Tests

```powershell
python -B -m unittest discover -s prototype2/tests -v
```

Tests use Python's built-in `unittest` library and replace the actual dialogs
with controlled selections. They read the existing `main` data; they do not
generate or modify datasets. Check the actual picker visually as well.

## Agreed later steps

- Separate Tkinter calendars for the exam range and no-exam dates.
- Initially show holidays and excluded weekdays from the selected settings.
- Read sessions, minimum exam gap, and invigilators per room from that file.
- Use existing data as read-only input and write outputs only to new locations.
- Connect the planner and independent checker in later approved steps.

Each step needs Krish's review before proceeding to the next.
