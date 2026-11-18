# Interactive workflow progress

## Completed 2026-11-17

Krish requested continuing from file selection into separate date-range and
no-exam-day calendars, then explicit timetable and seating confirmations.
No/Back must preserve choices. A failed timetable should show the existing
reason and allow the exam range to be increased. Reuse `why.txt` and the terms
guide. Existing files must remain untouched; use `main`, not `demo`.

Added only new files under `prototype2/workflow/`:

- `calendars.py`: editable date range, excluded days, preserved overrides and
  inherited weekday/holiday restrictions; separate Tkinter windows.
- `interface.py`: arrow menu, file/folder pickers, retained selections and
  confirmation/recovery choices. Uses existing picker/keyboard helpers unchanged.
- `flow.py`: Back/No/retry state transitions. No at either confirmation returns
  to inputs. Date/gap failure returns to the range calendar after the explanation;
  other failures offer dates or inputs. Earlier output files remain available.
- `planner.py`: selected-path loading using existing validators, in-memory
  effective settings, existing planning/failure logic, separate timetable and
  seating exports, and independent checker readers/rules.
- `run.py`: current entry point. Use Anaconda Python; the previously used uv
  interpreter lacks PyYAML. Anaconda already has both PyYAML and Tkinter.
- `engine/`: byte-identical copies of 8 prototype1 Python files and its terms
  guide. No input dataset was copied or generated.

Each successful attempt reserves a fresh directory under `prototype2/output/`.
It records effective settings and source paths/hashes, writes a checked timetable,
and only after Yes writes a complete seating/duty plan in a fresh subfolder.
All seating/duty feasibility is computed before announcing a successful timetable.
No output folder is reused. An export/check error marks its new output incomplete.
Failure folders contain only `why.txt`; the screen points to the copied terms
guide. Original inputs are only read; selections persist for the current process.

## Validation

- 16 workflow tests pass (see `test-results-20261117.txt`). The first test run
  found a test-fixture path one directory too high; corrected in the new test file.
- Existing `main` generates 56 papers, 454 room files, 8,750 occupied seats and
  908 duties. Exported seating/duties pass the independent checker.
- Tests cover No/Back preservation, date-failure recovery and extended-range
  retry, new-output uniqueness, unchanged original inputs, empty/missing paths,
  inherited holidays/weekdays, individual weekend exceptions and leap years.
- A real Tk widget check exercised range selection across leap day, holiday
  toggling and Back. Reviewed the two window-only images in `review/`.
- The full launcher was run in an interactive Windows terminal; menu rendering,
  navigation and Exit succeeded. Full native picker -> calendar -> generation
  interaction still needs Krish's review.
- Engine source copies and the guide were compared with prototype1 and are
  byte-identical. No existing source/data/docs were edited. No installations,
  commits or pushes. Test generation used disposable output folders only.

## Next human check

Run the new launcher, select existing main inputs, Continue to calendars, and
confirm that the date and no-exam windows open separately. At Generate timetable,
choose No and verify all input selections remain. Then generate and inspect the
reported paths. To review failure recovery, try a deliberately short range in
the calendar (without changing settings.yaml), read why.txt/terms, and extend it.
Wait for this review before adding another feature.
