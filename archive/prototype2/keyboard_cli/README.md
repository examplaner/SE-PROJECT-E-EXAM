# Keyboard input selection

Krish's requested change: "this 1 2 3 4 selection is bad"; use arrow keys like
Vite's setup. After selecting a file, "it should move to the next". Clear a
mistaken selection without deleting its file or losing the other choices.

This is a new entry point. The previous numbered menu and all existing data
and documentation are unchanged. It reuses that menu's file/folder pickers and
path checks by importing them; it does not copy or generate datasets.

From any PowerShell location on this machine:

```powershell
& "$env:APPDATA\uv\python\cpython-3.14-windows-x86_64-none\python.exe" -B "C:\Users\rs224\Downloads\SE-EXAM-clean\prototype2\keyboard_cli\menu.py"
```

- Up/Down: highlight an input or action. Navigation wraps at the ends.
- Enter: select or replace the highlighted input using its file/folder picker.
- Successful selection: move to the next missing input, or Continue if complete.
- Cancel in a picker: retain the old choice and highlight, return to the menu.
- Delete: clear only the highlighted input; stay there to choose its replacement.
- Escape or Ctrl+C: keep selections and return to the menu.
- Continue: recheck all paths and return the complete selection.
- Exit: end this session. Selections are only stored in memory.

The list shows a check mark beside selected inputs, with an ASCII fallback for
terminals that cannot display it. The highlighted row uses reverse video.
The picker starts in the existing `prototype1/data/main` dataset, as before.

Python's built-in `msvcrt` reads Windows keys without waiting for Enter.
`ctypes` enables Windows terminal drawing; the original terminal mode, cursor,
and screen are restored on exit. Tkinter supplies the native pickers. No new
third-party libraries are required. Run in an interactive Windows terminal,
not with redirected input/output. This is keyboard navigation, not mouse hover.

This step still only selects inputs. CSV-content validation, calendars, and
exam-plan generation belong to later approved steps.

## Tests

```powershell
python -B -m unittest discover -s prototype2/keyboard_cli/tests -v
```

Tests control key presses and picker responses while reading existing `main`
files. They create no datasets and do not modify existing files.
