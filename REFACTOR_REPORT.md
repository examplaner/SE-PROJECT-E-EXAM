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
| 7. demo cases | next |
| 8. prototype1 README, requirements, cleanup | to do |
| 9. prototype2 | to do |
| 10. final comparison, review, report | to do |

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

(filled in as pieces are finished)

## Differences and reasons

(none yet)

## Bugs found

(none yet)

## Lines of code

Before (from `git ls-files`, `wc -l`):

| File | Lines |
|---|---|
| prototype1/check.py | 910 |
| prototype1/duties.py | 311 |
| prototype1/errors.py | 8 |
| prototype1/loader.py | 104 |
| prototype1/main.py | 205 |
| prototype1/schedule.py | 516 |
| prototype1/seat.py | 616 |
| prototype1/validate.py | 467 |
| prototype1/tools/generate_data.py | 715 |
| prototype1/tests/test_*.py (6 files) | 1,845 |
| prototype2/input_selection.py | 139 |
| prototype2/keyboard_cli/menu.py, start.py | 205 |
| prototype2/workflow/calendars.py | 184 |
| prototype2/workflow/flow.py | 101 |
| prototype2/workflow/interface.py | 115 |
| prototype2/workflow/planner.py | 244 |
| prototype2/workflow/run.py | 28 |
| prototype2/workflow/setup.ps1, requirements-demo.txt | 94 |
| prototype2 tests (3 Python files, `check_calendar_windows.py`) | 510 |
| prototype2 demo cases (10 scripts + `_common.bash`) | 194 |
| prototype2/workflow/engine/*.py (copy of prototype1) | 3,137 |

## Not checked

(filled in at the end)
