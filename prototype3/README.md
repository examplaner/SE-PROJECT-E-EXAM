# Exam planner (prototype 3)

Give it the exam data, and it makes the whole exam plan:

1. **a date sheet:** which paper is on which day, morning or evening;
2. **a seating plan:** a picture of every room in use, showing who sits where;
3. **invigilation duties:** which teachers sit in each room.

The plan follows every rule in [`docs/prototype1_model_spec.md`](docs/prototype1_model_spec.md), or the tool
says in a few lines why no plan is possible. A separate checker re-reads a plan and checks it against the rules
on its own.

There are two ways to run it: the **app**, where you pick the files and dates in menus and calendars, and the
**command line**, where you give it a folder.

## Set up

You need Python 3.10 or newer with Tkinter. In a terminal, in the `prototype3/` folder:

**Windows (PowerShell):**

```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Linux and Mac:**

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

That installs PyYAML (settings files), questionary (the app's arrow-key menus) and pytest (the tests).
Tkinter comes with Python on Windows and from python.org on Mac; on Debian or Ubuntu it is
`sudo apt install python3-tk`. The commands below are run from `prototype3/` with the environment active.

## The app

```
python app.py
```

Run it in an interactive terminal: PowerShell, Command Prompt or Windows Terminal on Windows (Git Bash's
window can't show the menus), the normal terminal on Linux and Mac.

1. **Inputs.** Up/Down move and Enter chooses. Enter on an input opens its picker, which starts in
   `data/main`; after a choice the menu moves on to the next input not chosen yet. Choose `sections.csv` for
   the section information and the `sections` folder for the student lists. Cancel in a picker keeps the old
   choice. "Clear a choice" clears one choice; its file is never touched. Ctrl+C keeps every choice.
2. **Exam range.** In the first calendar, click the first exam day, then the last. Back returns to the inputs.
3. **No-exam days.** Red days have no exams. Click a day to switch it. Back returns to the range.
4. **Make the timetable?** Yes makes the whole plan, so it checks seats and teachers too, then saves and checks
   the timetable. No returns to the inputs.
5. **Write the seating plan?** Yes writes the seating plan and duties and checks the whole plan.

If no plan is possible, the app shows the reason and goes back to the dates or the inputs, with every choice
kept. Input files are only read. Each run gets a new folder under `output/`:

```
output/2026-11-19_10-15-00_x1y2z3/
├── settings.yaml        the settings of this run, with the dates from the calendars
├── sources.json         the input files used, with a fingerprint (SHA-256) of each
├── timetable/           schedule.csv, basis.txt and terms.md
└── seating_x4y5z6/      the full plan, as the command line writes it (below)
```

## The command line

```
python engine/main.py data/tiny
```

```
Input OK: 2 sections, 16 students, 8 course codes (7 papers), 3 rooms, 9 teachers.
Timetable basis: biggest papers first; each paper goes into the session where it adds the fewest rooms (on a tie, the session with fewer students).
Seating basis: one paper per room, with the mix of room sizes that needs the fewest rooms; 6 rooms hold one paper and 1 holds two (two papers' leftovers joined, or mixed where the rooms ran out).
If a word in these lines is not clear, read terms.md in the plan folder.
Scheduled 7 papers on 3 days, 2026-11-02 to 2026-11-06.
Fullest session: 2026-11-02 morning, 16 of 45 seats (29 left).
Seating: 7 room files (1 with two papers). Most rooms in one slot: 3 of 3 (2026-11-06 morning).
Duties: 14. Each regular teacher has 1 to 2; PhD scholars have 0. Teachers with both shifts on one day: 0 times.
Wrote output/2026-11-19_02-43-53
```

Then check the plan, naming the folder from the last line (on Windows it prints with `\`; both work):

```
python engine/check.py data/tiny output/2026-11-19_02-43-53
```

```
Plan check: no problems. 7 papers, 7 room files, 48 seats, 14 duties checked.
```

`--output <folder>` puts plan folders somewhere other than `output/`. Every run makes a new folder named by
the time of the run, so nothing is overwritten:

```
output/2026-11-19_02-43-53/
├── schedule.csv          the date sheet: date, session, paper, its course codes, students
├── duties.csv            one row per teacher per room per session
├── basis.txt             the two "basis" lines printed above
├── terms.md              what the words of the plan mean, with small examples
└── daywise_seating_plans/<date>/<session>/<room>.csv
```

A room CSV is a picture of the room as the invigilator at the front sees it: row 1 is the front row, column 1
is on the left, a cell reads `paper:student`, and a blank cell is an empty seat. Only rooms in use get a file.
If no plan is possible, the folder holds only `why.txt`, with the reason that was printed.

| Exit code | `engine/main.py` | `engine/check.py` |
|---|---|---|
| 0 | a plan was written | the plan breaks no rule |
| 1 | the input is invalid; every problem is listed with its file and row | the input or plan folder can't be read |
| 2 | no plan is possible; the reason is in `why.txt` | the folder holds only `why.txt` |
| 3 | | the plan breaks a rule; every problem is listed under its rule |

## The datasets

| Folder | What it is |
|---|---|
| `data/tiny` | The small example: 2 cohorts, 16 students, 3 rooms, 9 teachers, 2 to 6 Nov. Small enough to check by hand. |
| `data/main` | The realistic example: 1,600 students in 10 cohorts, 56 papers, 36 rooms, 85 teachers, 2 to 20 Nov. Made up, not real data. |
| `data/impossible/` | Seven copies of `tiny`, each broken on purpose so no plan is possible ([its README](data/impossible/README.md)). |

`python tools/generate_data.py` writes `data/tiny` and `data/main`. Its numbers are at the top of the script,
and the same numbers always give the same files. The input files and their columns are in
[`docs/data_design_spec.md`](docs/data_design_spec.md) sections 2 and 3.

## Tests

```
python -m pytest tests/unit
```

The unit tests use scripted answers instead of a person, so no menu, picker or calendar opens. The windows
themselves need a person to try them.

The demo cases run the planner and the checker from outside, the way a person would, and check the exit codes
and messages. They need bash: Git Bash on Windows, the normal terminal on Linux and Mac. Run one, or all ten:

```
bash tests/demo/04-gap-window.sh
for case in tests/demo/[0-9]*.sh; do bash "$case" || break; done
```

They use `python`, or `python3` if there is no `python`; set `PYTHON` to use another one.

The same ten cases are in Python too, in `tests/demo/python_tests/`, for a computer without bash. Each one does
what its bash case does, step for step. Run one, or all ten:

```
python tests/demo/python_tests/04_gap_window.py
python tests/demo/python_tests/run_all.py
```

## The code

| File | What it does |
|---|---|
| `app.py` | Starts the app. |
| `flow.py` | The app's steps in order, with their back and retry loops. |
| `terminal.py` | How the app asks: questionary menus and yes/no questions, the pickers and the calendars. |
| `inputs.py` | The nine inputs, the inputs menu, the path checks and the file and folder pickers. |
| `calendars.py` | The two calendars and the dates behind them. |
| `planner.py` | Runs the engine on the chosen files and writes each run's folder. |
| `engine/main.py` | The command line: checks the input, runs the three steps, writes the plan, prints the numbers. |
| `engine/loader.py` | Reads the input files. |
| `engine/validate.py` | Checks the input: first that every file can be read, then the data inside. |
| `engine/exam.py` | Builds what the steps need, once: papers, rooms, sections, who teaches what, exam days. |
| `engine/schedule.py` | Step 4: a date and session for each paper. |
| `engine/seat.py`, `engine/room_mix.py` | Step 5: a seat for each student; `room_mix.py` picks the mix of room sizes. |
| `engine/duties.py` | Step 6: teachers for each room. |
| `engine/writer.py` | Writes the plan folder, or `why.txt`. |
| `engine/errors.py` | `NoPlan`, raised when no plan is possible. |
| `engine/check.py` | The checker. It imports nothing from the planner, so a bug there can't hide from it. |

The planner is greedy and plain on purpose, so every step can be explained, and the same input always gives
the same plan. What is left for later is in the model spec, section 2.
