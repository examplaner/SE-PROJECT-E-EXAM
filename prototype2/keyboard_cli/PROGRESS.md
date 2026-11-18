# Keyboard menu progress

## 2026-11-17

Krish rejected entering numbered choices and requested navigation like Vite's
setup. He chose advancing to the next missing input after selection. For a
mistaken file, Enter replaces the selection and Delete clears it without
deleting the file; Cancel preserves previous choices so progress is not lost.

Implemented in new `menu.py`, importing the existing `input_selection.py`
pickers/checks without modifying that file. Up/Down navigates, Enter selects,
Delete clears only the highlighted input and stays there, Cancel preserves
the prior choice, and Continue checks completeness and current path usability.
Exit is a separate row. Selected inputs show a check mark. No mouse hover.

Validation:
- 12 new keyboard-menu tests pass.
- All 10 existing input-selection tests pass.
- Interactive Windows terminal check: Up/Down, Delete, Enter on Exit, redraw,
  and clean exit succeeded. Native picker interaction remains for human review;
  picker responses were simulated in the tests.
- Compared SHA-256 hashes for 313 pre-existing source/data/documentation files
  (excluding Git internals, generated outputs, and Python bytecode): no changes.
- No datasets created, no packages installed, no commits or pushes.

Only this step is implemented. Calendars, content validation, and connection
to the planner/checker still need subsequent approval. Choices remain in memory
for one run; there is no cross-session persistence.

Next: Krish runs the new menu, selects Teachers, observes movement to Courses,
moves back to Teachers and presses Delete. Verify only Teachers is cleared,
the highlight stays on Teachers, and the selected file remains on disk.
Wait for feedback before starting another step.
