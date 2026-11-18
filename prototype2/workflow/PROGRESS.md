# Interactive workflow progress

## 2026-11-19

Made CLI planning failures easier to spot with a heading, the full engine
reason, a labeled `why.txt` path, and a note explaining when `basis.txt` is
created. Successful timetable and seating saves now print their `basis.txt`
paths. The terminal display is ready for Krish's review.

Added the grouped Git Bash runner. Verified the three validation examples,
seven impossible datasets, each named test group, and all 191 automated cases
with both full-suite command forms. A temporary corrected fixture in place
of the deliberately bad input produced the expected demo failure.

Added a dedicated `no-plan` runner group for Step 7 automated tests and
mapped test commands to the recorded prototype steps in `BASH_COMMANDS.md`.

Added a reusable Stage 2 registration example in `prototype1/data/impossible`.
Verified the single row 50 error and its correction with the live validator.
All 20 tests in the no-plan and live-validation suites passed.

## 2026-11-18

Added live two-stage validation to the workflow input menu. A bad header or
single-file data error preserves an earlier choice. Cross-file errors appear
when their inputs are available and either file can be replaced. Continue
rereads the selection before opening calendars. Generation checks the selected
source settings and effective calendar settings. Eight new tests cover picker
order, rejection, correction, pending relationships and revalidation.
The class walkthrough is in `TEST_CASES.md`. The stage 1 header report,
line wrapping, dismissal and return to the menu were exercised in a Windows
terminal with a controlled picker response.

Documented all 183 active test cases in `TEST_CASES.md`. The 145 engine tests
and the 10 picker, 12 keyboard and 16 workflow tests passed. Reproduced the
two input-validation failures, the short-window failure, a clean tiny plan
and a damaged seating plan in a temporary directory.

Added `bin/examplan.cmd` and registered its folder on this Windows account's
user PATH. Verified PowerShell and Command Prompt find `examplan` from the
user's home folder. The input menu opened and Exit returned success.

The second confirmation and progress message now name both the seating plan
and teacher duties. One Yes saves both. All 16 workflow tests passed, including
the export check for 454 room files and 908 duty assignments on the main dataset.

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
