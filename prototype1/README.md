# Exam planner (prototype 1)

Give it a folder of exam data, and it makes the whole exam plan in a new folder:

1. **a date sheet:** which paper is on which day, morning or evening;
2. **a seating plan:** a picture of every room in use, showing who sits where;
3. **invigilation duties:** which teachers sit in each room.

The plan follows every rule in [`docs/prototype1_model_spec.md`](docs/prototype1_model_spec.md),
or the tool says in a few lines why no plan is possible. A separate checker re-reads a plan and checks it
against the rules on its own.

## Set up

You need Python 3.10 or newer. In a terminal, in the `prototype1/` folder:

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

That installs PyYAML (to read the settings files) and pytest (for the tests). Nothing else: no database,
no internet and no solver library. The commands below are run from `prototype1/` with the environment
active.

## Run

```
python main.py data/tiny
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
python check.py data/tiny output/2026-11-19_02-43-53
```

```
Plan check: no problems. 7 papers, 7 room files, 48 seats, 14 duties checked.
```

`python main.py data/main` plans the realistic dataset. `--output <folder>` puts plan folders somewhere other
than `output/`.

## What comes out

Every run makes a new folder named by the time of the run, so nothing is overwritten:

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

| Exit code | `main.py` | `check.py` |
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

The demo cases run the planner and the checker from outside, the way a person would, and check the exit codes
and messages. They need bash: Git Bash on Windows, the normal terminal on Linux and Mac. Run one, or all ten:

```
bash tests/demo/04-gap-window.sh
for case in tests/demo/[0-9]*.sh; do bash "$case" || break; done
```

They use `python`, or `python3` if there is no `python`; set `PYTHON` to use another one.

## The code

| File | What it does |
|---|---|
| `main.py` | The command line: checks the input, runs the three steps, writes the plan, prints the numbers. |
| `loader.py` | Reads the input files. |
| `validate.py` | Checks the input: first that every file can be read, then the data inside. |
| `exam.py` | Builds what the steps need, once: papers, rooms, sections, who teaches what, exam days. |
| `schedule.py` | Step 4: a date and session for each paper. |
| `seat.py`, `room_mix.py` | Step 5: a seat for each student; `room_mix.py` picks the mix of room sizes. |
| `duties.py` | Step 6: teachers for each room. |
| `writer.py` | Writes the plan folder, or `why.txt`. |
| `errors.py` | `NoPlan`, raised when no plan is possible. |
| `check.py` | The checker. It imports nothing from the planner, so a bug there can't hide from it. |

The planner is greedy and plain on purpose, so every step can be explained, and the same input always gives
the same plan. What prototype 1 leaves for later is in the model spec, section 2.
