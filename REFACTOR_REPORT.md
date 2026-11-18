# Refactor report: prototype1 and prototype2

The job is Ishan's brief `agents/tasks/refactor.md`: the same behaviour with simpler code. This file is where the work
is picked up after a break. Branch `abhishek/refactor`, made from `main` (= tag `pre-refactor`, commit `e621c25`).

## Status

| Piece | State |
|---|---|
| 1. Setup and baseline | done |
| 2. prototype1 loader and validate | done |
| 3. prototype1 planning engine | done |
| 4. `check.py` | done |
| 5. generator | done |
| 6. prototype1 unit tests | done (134 pass) |
| 7. demo cases | done |
| 8. prototype1 README, requirements, cleanup | done |
| 9. prototype2 | done |
| 10. final comparison, review, report | done |

## The plan as accepted

Accepted by the user on 2026-11-19, with one addition the same day: use names that make sense to someone new
(for example, not "tiny" where a plain name can be chosen).

### Why
- The same things are built again and again: papers (`schedule.build_papers`, 3 times a run), `section_of` (3 times),
  teaching (2 times), two copies of "one-paper seats", two date parsers.
- Callbacks of callbacks: `schedule.room_check_for` -> `teacher_room_check` -> `papers_short`, passed through
  `seat.make_seating` and `seat.seat_slot`.
- Wrappers and dead guards, long history docstrings and banner comments.
- prototype2 has three entry points, Windows-only `msvcrt`/`ctypes`, and re-implements the engine's and the
  checker's loading for picked files.
- The generator has its own 160-line copy of the input checks.

### prototype1: modules and functions
Same command line, input folder, output layout, printed text and exit codes.

| Module | Functions |
|---|---|
| `main.py` | `main()`: validate, build the exam, schedule, seat, duties, write, print; `summary(data)`; `print_numbers(...)` |
| `loader.py` | `CSV_COLUMNS`; `input_paths(input_dir)`: folder -> path of each input; `read_csv_lines`, `read_table`, `read_yaml`; `as_date` (the engine's one date parser); `load(paths)` |
| `validate.py` | `Problem`, `format_report`; `check_folder(input_dir)`; `check_files(paths)`; `check_csv_file`; `check_data(data)` and one check per file |
| `exam.py` (new) | `Paper`, `Room`, `Exam`; `build_exam(data)`: everything the three steps need, built once; `build_papers`, `build_teaching`, `exam_days` |
| `schedule.py` | `make_schedule(exam)` -> (placements, way, failed ways); `check_before_scheduling`; `most_papers_in_window`; `place_papers`; `choose_slot`; `check_session` (cached); `build_clashes`; `basis_line`; `fullest_session` |
| `seat.py` | `RoomPlan`; `seat_slot(papers, exam)`; `make_seating`; `alone_seats`, `partner_seats`, `seat_room`; `paper_queues`, `section_runs`; `seat_alone`; `seat_best`, `seat_best_for_teachers`; `seat_with_mixing`; `join_leftovers`, `leftover_rooms`, `best_join`; `basis_line`, `cell_text` |
| `room_mix.py` (new, out of `seat.py`) | `room_sizes`, `room_options`, `fewest_rooms`, `best_combination` |
| `duties.py` | `rooms_for_paper`, `teachers_without_room`, `make_duties`, `staff_slot`, `own_paper_rooms`, `place_teacher`, `best_first`, `duty_summary` |
| `writer.py` (new, out of `main.py`) | `new_plan_folder`, `write_why`, `write_schedule`, `write_seating`, `write_duties`, `write_basis` |
| `errors.py` | `NoPlan` |
| `check.py` | imports nothing from the engine; same stages, every check adds to `Problems` the same way; `check_duties` split in four |
| `tools/generate_data.py` | same files byte for byte; runs `validate.py` instead of its own copy of the checks |

### prototype2: one app
`app.py` (entry point), `flow.py` (the steps and back/retry loops), `terminal.py` (questionary menus and prompts),
`inputs.py` (pickers, path checks, inputs menu), `calendars.py` (Tkinter calendars), `planner.py` (runs the engine on
the picked files), `engine/` (exact copy of prototype1's engine and checker), its own copy of the datasets,
`requirements.txt`, `tests/unit/`. `input_selection.py`, `keyboard_cli/`, `workflow/`, Windows-only setup files,
`PROGRESS.md` and `handoff.md` go.

### Tests
- `prototype1/tests/unit/` (pytest) covers the old tests' behaviour through the new functions; old tests deleted.
- `prototype1/tests/demo/`: Himank's 10 cases, moved, pointed at prototype1, each readable top to bottom.
- `prototype2/tests/unit/`.

### Order of work
As in the status table above, one commit per piece.

## Baseline (before any change), 2026-11-19

- Old copy: `git archive pre-refactor` exported to a scratch folder outside the repo.
- Python 3.13.15 on Windows 11, in a virtual environment with `PyYAML==6.0.3`, `pytest==9.1.1`,
  `questionary==2.1.1`.
- Old tests: prototype1 145 passed; prototype2 `workflow/tests` 16 passed, `tests` and `keyboard_cli/tests` OK;
  all 10 demo cases pass (Git Bash).
- Old generator: writes `data/tiny` and `data/main` byte for byte as they are in this checkout (Windows,
  `core.autocrlf=true`).

### How the comparison works
A script outside the repo (not committed) runs the old copy and the new code side by side:
- **datasets:** `main.py` on `data/tiny`, `data/main` and the 7 folders of `data/impossible/`; compares the exit
  code, the printed text (timestamp hidden) and every file of the output folder byte for byte;
- **inputs:** 34 broken inputs (every case of the old `test_validate.py` and demo case 02, plus more for every
  check): exit code, printed text, rules named;
- **plans:** 39 broken or clean plans made from `tiny` by the old code (every case of the old `test_check.py` and
  demo cases 05, 07 to 10, plus more): the old and the new `check.py` on the same plan, exit code, printed text,
  rules named;
- **cross:** the old `check.py` on the new plans and the new `check.py` on the old plans, `tiny` and `main`.

## Results

All on Windows 11, Python 3.13.15, 2026-11-19, against the old copy exported from tag `pre-refactor`.

### 1-3. The old and the new `main.py` on every dataset

Exit code, printed text (timestamp hidden) and every file of the output folder, byte for byte:

| Dataset | Exit code old / new | Printed text | Output files |
|---|---|---|---|
| `data/tiny` | 0 / 0 | same | 11 of 11 the same |
| `data/main` | 0 / 0 | same | 458 of 458 the same |
| `data/impossible/duty_room_full` | 2 / 2 | same | `why.txt` the same |
| `data/impossible/no_day_fits` | 2 / 2 | same | `why.txt` the same |
| `data/impossible/no_exam_days` | 2 / 2 | same | `why.txt` the same |
| `data/impossible/paper_too_big` | 2 / 2 | same | `why.txt` the same |
| `data/impossible/too_few_teachers` | 2 / 2 | same | `why.txt` the same |
| `data/impossible/waiting_paper` | 2 / 2 | same | `why.txt` the same |
| `data/impossible/window_too_short` | 2 / 2 | same | `why.txt` the same |

The datasets don't reach every path of the planner, so random variants of `tiny` and `main` were also run
through both (other windows, holidays, gap, invigilators per room, rooms added, removed or reshaped, more
teachers and teaching rows): **960 variants, 0 differences** in exit code, printed text or files, 290 of them
after the review's changes. They reached
all three ways of choosing sessions and the "duty room", "gap", "seats" and "paper placement" reasons. (One
more run of 290 variants also gave 0 differences, but another comparison wrote to the same output folder at
the same time, so it is not counted.)

### 4. Each checker on the other's plans

| Plan | Old `check.py` on the new plan | New `check.py` on the old plan |
|---|---|---|
| `tiny` | 0, no problems (7 papers, 7 room files, 48 seats, 14 duties) | 0, the same |
| `main` | 0, no problems (56 papers, 454 room files, 8,750 seats, 908 duties) | 0, the same |

### 5. Broken inputs and broken plans

- **34 broken inputs**: every case of the old `test_validate.py` and demo case 02, plus cases for every other
  check (missing roster folder, extra roster, blank IDs, BOM and blank lines, a file that is not UTF-8, bad
  settings and constraints of every kind, and more). The old and new `main.py` give the same exit code, the
  same rules and the same printed text in all 34.
- **39 broken plans and 1 clean one**: every case of the old `test_check.py` and demo cases 05, 07, 08, 09 and
  10, plus more (a third paper in a room, outside the window, not an exam weekday, a wrong student count, an
  unknown paper, a paper twice or missing, bad duty rows, a bad header, an empty room file, stray folders, a
  missing seating folder, unreadable input, a missing plan folder, a seat in another slot) and a folder holding
  only `why.txt`. The old and new `check.py` give the same exit code (0, 1, 2 or 3), the same rules and the
  same printed text in all 40.
- The 10 demo cases pass on the new code (Git Bash on Windows).

### 6. The generator

The new `tools/generate_data.py` writes the same 50 files as the old one, byte for byte, and prints the same
summary. Run in place, it rewrites `data/tiny` and `data/main` with no byte changed (`git status` clean).

### 7. prototype2

prototype2's planning without menus or calendars (`planner.generate_timetable` and `generate_seating` on its
own copies of the datasets, with the dates the calendars start with) gives the same files as prototype1's
`main.py`: 11 of 11 for `small_example` against `data/tiny`, 458 of 458 for `realistic_example` against
`data/main`, and the checker passes both. A unit test in prototype2 checks the same against its
`engine/main.py`. `engine/` is byte for byte the same as prototype1's modules, `check.py` and `docs/terms.md`,
and `data/` the same as prototype1's `data/tiny` and `data/main`.

### Tests

| Suite | Result |
|---|---|
| prototype1 `tests/unit` | 134 passed |
| prototype1 `tests/demo` | 10 of 10 pass |
| prototype2 `tests/unit` | 32 passed |

The real questionary menus were also driven with scripted key presses (default highlight, Down, Up going
round, Enter, Ctrl+C, yes and no), and `python app.py` was started in a real PowerShell window, where the
inputs menu showed as it should.

## Differences and reasons

1. **An impossible date in a YAML file** (`holidays: [2026-11-40]`) made both `main.py` and `check.py` stop
   with a Python traceback. Now `main.py` reports `settings.yaml: cannot be read as YAML (day is out of range
   for month)` and `check.py` says it can't read the file. Reason: a real bug (below). The exit code stays 1
   in both, and no rule of the specs changes, so there is no change log row.
2. **The generator's report when its own data is broken** now uses the planner's input checks and report
   (`validate.py`) instead of its own copy of them. Reason: the brief's "remove repeated code". With the data
   in the specs nothing changes: it prints "checks passed" as before.
3. **prototype2, clearing a choice.** The Delete key is now a "Clear a choice" row in the inputs menu: it lists
   the chosen inputs, clears the one picked (its file is not touched), and the menu returns to that input.
   Reason: questionary, which the brief asks for, has no way to add a key such as Delete without reaching into
   prompt_toolkit's internals, which no one could explain.
4. **prototype2, other menu changes that come with questionary.** Escape no longer goes back in the terminal
   menus (Ctrl+C does, and keeps every choice; Escape still closes a calendar as Back). The menus print in the
   terminal instead of redrawing a separate screen. "Make the timetable now?" and "Write the seating plan?"
   are yes/no questions instead of two-row menus. The highlighted input's full path shows as the row's
   description.
5. **prototype2, messages.** A picked CSV file with a bad header is named by its file name instead of its full
   path. Started without a terminal, the app says to run it in a terminal window (it used to say a Windows
   terminal; it now runs on all three systems).
6. **Guards for cases that can't happen** went, each checked against the validated input: the `size > 0` check
   and the "no rooms" check of the room search (a dataset with no rooms stops at the cheap seat check before
   seating), skipping papers with no students (every course code has a registration), `join_leftovers`' check
   for two-paper rooms (only one-paper seatings reach it), `fullest_session` with no placements, and
   `rank_of.get` for teachers who must be in `teachers.csv`. Behaviour on every valid input is unchanged (all
   comparisons above).
7. **Demo case 01** is renamed `01-realistic-plan.sh` (was `01-full-main-plan.sh`), so its name says which
   dataset it uses. It checks what it checked before.
8. **prototype2, calendar days** are drawn as labels that react to a click, not as buttons. Reason: macOS draws
   buttons itself and ignores their colour, so the red no-exam days and the blue range would not show there
   (found in the review below; not tried on a Mac). They look a little flatter on Windows; what a click does is
   unchanged, and a day outside the range is grey and does nothing, as the disabled button did.

## Bugs found

1. **Fixed:** the impossible YAML date crash above (`validate.check_yaml_file`, `check.read_input_yaml`).
2. **Not fixed, behaviour kept:** the generator writes CSV files with `\r\n` line ends on every system and YAML
   files with the system's own line ends. On Linux and Mac a checkout has `\n` everywhere, so after running
   the generator git shows every CSV file as changed (the content is the same). The brief asks for the same
   files as before, so this stays; writing `\n` everywhere would fix it.
3. **Not fixed, outside what may change:** `data/impossible/README.md` names old test paths that are gone, and
   the brief says no file under `data/` changes. The new tests are
   `tests/unit/test_seat.py::test_a_room_never_holds_a_third_paper`,
   `tests/unit/test_duties.py::test_one_own_paper_with_no_room_is_no_plan` and
   `tests/unit/test_duties.py::test_no_plan_when_two_own_papers_need_different_rooms`.
4. **Not fixed, a note:** that README also says `main.py`'s "Rule: papers" is never reached. It is, for an
   input folder whose files hold only headers (no sections, students or courses): it passes the checks and then
   has nothing to schedule. The message is still right.
5. **Not fixed, cosmetic:** "All 1 rooms together give 12 seats" (the message is kept as it was).

## Code review

When the code was written, a fresh subagent went through it with `agents/skills/code/checklist.md` and the
brief, without editing anything. It reported 56 points. What was done with them:

- **Fixed, a real bug:** demo case 03 compared `wc -l`'s count as text; Mac's `wc` puts spaces before the
  number, so the case would fail there. It now compares numbers.
- **Fixed, an OS problem:** the calendar colours on macOS (difference 8 above).
- **Fixed, a wrong comment:** `inputs.py` said its late Tkinter import let the app run without Tkinter, which
  was not true; Tkinter is now imported at the top. The `CalendarDialog` docstring said Back keeps the dates as
  they were; it keeps what was clicked, as the old code did, and now says so.
- **Done, plainer code:** nested comprehensions, `x[0]`/`x[1]` reads of tuples, a set-subset `<=`, `not a & b`
  without brackets, one-letter names (`t`, `r`, `c`, `n`, `k`), a sort key with a `True`/`False` first part and
  no reason, a 55-line `staff_slot` (now three functions), the `(rooms, empty, chosen)` triples in `room_mix.py`,
  `setdefault` used as a lookup in `check.py`, a duplicate weekday list, a two-paper room count written twice,
  missing reasons (`|| code=$?`, `-B`, why not `sed -i`, why `seat_room()` empties its list, why
  `write_basis` copies its list, `unsafe_ask()`), three copies of a cached "plan this dataset" helper and two
  of `replace_once` in the tests (now one each in `conftest.py`), a docstring opening with four quotes, an
  unused test argument, and magic numbers.
- **Kept, judgment calls:** sort-key lambdas (common Python, and each says what it sorts by); `or` for an empty
  fallback in message texts; the 8 and 9 arguments of two checker functions (grouping them would change the
  checker's structure for little gain); the `TERMS_FILE.is_file()` guard (a missing `terms.md` should still
  give a plan, as before); `summary()` counting papers from the files (it runs before the exam is built, as
  before); `pick_inputs()` taking its picker and check as arguments, so its tests need no patching; the copy of
  the settings in `ExamCalendar.from_settings()`.

After these changes every comparison was run again: the 9 datasets, 34 broken inputs, 40 plans, the cross
checks, prototype2 against prototype1, the generator, all unit tests, the 10 demo cases, and 290 more random
variants: all the same as the old code.

## Not checked

- **Linux and Mac:** everything was run on Windows 11 only. The code uses `pathlib` and `encoding="utf-8"`,
  and the demo cases use only bash, `grep`, `sed`, `mv`, `cut`, `wc`, `tr` and `mktemp`, but none of it was
  run there.
- **Python versions** other than 3.13.15.
- **prototype2 by a person:** the pickers, both calendars and a full walk through the menus. The steps to try
  them are below.
- **Git Bash's own window** (mintty) can't show questionary menus, because Windows Python sees no console
  there; the app then says to use PowerShell, Command Prompt or Windows Terminal. `winpty python app.py` may
  work in Git Bash, but was not tried.

### Trying prototype2 by hand

Set up as `prototype2/README.md` says, then run `python app.py` in PowerShell (and once on Linux or Mac).

1. The inputs menu shows nine inputs, all "not chosen", Teachers highlighted. Up from Teachers goes round to
   Exit.
2. Enter on Teachers: a file picker opens in `data/realistic_example`. Choose `teachers.csv`. The row shows
   `[x] Teachers: teachers.csv`, its full path shows under it, and Courses is highlighted.
3. Choose the rest: `sections.csv` for Section information, the `sections` folder for Student lists (a folder
   picker opens), `teaching.csv` for Who teaches what, then `settings.yaml` and `constraints.yaml`.
4. Enter on Teachers again and Cancel the picker: the choice stays. Choose `settings.yaml` there: refused
   ("ending in .csv"), and the old choice stays.
5. "Clear a choice", then Teachers: it is cleared and highlighted, and `teachers.csv` is still on disk. Choose
   it again.
6. Ctrl+C in the menu: every choice stays.
7. "Continue to exam dates": the range calendar opens on November 2026 with 2 to 20 Nov in blue. Click "Choose
   end date", then 4 Nov, then Continue.
8. The no-exam-days calendar: weekends and 11 Nov are red. Click 11 Nov to allow it, and again to exclude it.
   Back returns to the range calendar with 2 to 4 Nov kept; Continue twice.
9. "Make the timetable now?" Yes: no plan is possible ("Rule: gap"); the reason and the paths of `why.txt` and
   `terms.md` show. Enter goes back to the range calendar, with every input still chosen.
10. Set the end date back to 20 Nov, Continue twice, Yes: the timetable is saved and its path shown.
11. "Write the seating plan?" Yes: the seating plan, the duties and "Plan check passed: 56 papers, 454 room
    files, 8750 seats, 908 duties." show. "Back to the inputs" keeps every choice; Exit ends the app.
12. In `output/`, the run's folder holds `settings.yaml`, `sources.json`, `timetable/` and one `seating_*`
    folder; the run with no plan has a folder of its own holding `why.txt`. No input file changed (`git status`
    clean).
13. Close a calendar window with its X, and press Escape in one: both act as Back.

## Lines of code

From `git ls-files` and `wc -l`, before (tag `pre-refactor`) and after (this branch).

| File | Before | After |
|---|---|---|
| prototype1/main.py | 205 | 116 |
| prototype1/loader.py | 104 | 120 |
| prototype1/validate.py | 467 | 413 |
| prototype1/exam.py | new | 139 |
| prototype1/schedule.py | 516 | 367 |
| prototype1/seat.py | 616 | 508 |
| prototype1/room_mix.py | new | 116 |
| prototype1/duties.py | 311 | 300 |
| prototype1/writer.py | new | 89 |
| prototype1/errors.py | 8 | 7 |
| **prototype1 planner** | **2,227** | **2,175** |
| prototype1/check.py | 910 | 897 |
| prototype1/tools/generate_data.py | 715 | 564 |
| prototype1 unit tests | 1,845 (`tests/test_*.py`) | 1,430 (`tests/unit/`) |
| demo cases | 194 (in prototype2) | 360 (`prototype1/tests/demo/`, a comment above every step) |
| prototype2 app | 1,016 (`input_selection.py`, `keyboard_cli/`, `workflow/*.py`) | 919 (`app.py`, `flow.py`, `terminal.py`, `inputs.py`, `calendars.py`, `planner.py`) |
| prototype2 setup files | 94 (`setup.ps1`, `requirements-demo.txt`) | 3 (`requirements.txt`) |
| prototype2 tests | 510 | 481 |
| prototype2 engine copy | 3,137 | 3,072 |

Shorter was not the aim: some modules grew where a trick became plain loops, or one long function became
several short ones.

## Handing over

Push the branch yourself (an AI assistant never pushes):

```
git push -u origin abhishek/refactor
```

Then open a pull request into `main` for Ishan.
