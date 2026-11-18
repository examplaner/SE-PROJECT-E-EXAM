# Exam planner app (prototype 2)

The exam planner of prototype 1, driven from menus instead of a command line. Nobody types a path:

- the nine inputs are chosen in file and folder pickers;
- the exam range and the no-exam days are chosen in two calendars, with the settings file's weekdays and
  holidays already marked;
- the app asks before it makes the timetable, and again before it writes the seating plan;
- if no plan is possible it shows the planner's reason, and you change the dates or the inputs without
  starting over.

The planning is prototype 1's: `engine/` is an exact copy of its planner and checker, so the same inputs give
the same plan. `data/` holds copies of its two example datasets, so this app runs on its own.

## Set up

You need Python 3.10 or newer with Tkinter. In a terminal, in the `prototype2/` folder:

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

That installs PyYAML (settings files), questionary (the arrow-key menus) and pytest (the tests). Tkinter comes
with Python on Windows and from python.org on Mac; on Debian or Ubuntu it is `sudo apt install python3-tk`.

## Run

```
python app.py
```

Run it in an interactive terminal: PowerShell, Command Prompt or Windows Terminal on Windows (Git Bash's
window can't show the menus), the normal terminal on Linux and Mac.

1. **Inputs.** Up/Down move and Enter chooses; the menus go round at the ends. Enter on an input opens its
   picker, which starts in `data/realistic_example`; after a choice the menu moves on to the next input not
   chosen yet. Choose `sections.csv` for the section information and the `sections` folder for the student
   lists. Cancel in a picker keeps the old choice. "Clear a choice" clears one choice; its file is never
   touched. Ctrl+C keeps every choice.
2. **Exam range.** In the first calendar, click the first exam day, then the last. Back returns to the inputs.
3. **No-exam days.** Red days have no exams. Click a day to switch it. Back returns to the range.
4. **Make the timetable?** Yes makes the whole plan, so it checks seats and teachers too, then saves and checks
   the timetable. No returns to the inputs.
5. **Write the seating plan?** Yes writes the seating plan and duties and checks the whole plan.

Choices stay in memory while the app runs. The settings file and the other inputs are only read.

## What comes out

Every run gets a new folder under `output/`, named by the time; nothing is ever overwritten:

```
output/2026-11-19_10-15-00_x1y2z3/
├── settings.yaml        the settings of this run, with the dates from the calendars
├── sources.json         the input files used, with a fingerprint (SHA-256) of each
├── timetable/           schedule.csv, basis.txt and terms.md
└── seating_x4y5z6/      the full plan: schedule.csv, duties.csv, basis.txt, terms.md
                         and daywise_seating_plans/<date>/<session>/<room>.csv
```

Each Yes to the seating plan makes a new `seating_*` folder. When no plan is possible, the run's folder holds
only `why.txt`. A folder that could not be finished holds `INCOMPLETE.txt`. The files are described in
prototype 1's `README.md`.

## Tests

```
python -m pytest tests/unit
```

They use scripted answers instead of a person, so no menu, picker or calendar opens. One test checks that the
app's plan files are byte for byte the same as the command line's (`engine/main.py`). The windows themselves
need a person to try them.

## The code

| File | What it does |
|---|---|
| `app.py` | Starts the app. |
| `flow.py` | The steps in order, with their back and retry loops. |
| `terminal.py` | How the app asks: questionary menus and yes/no questions, the pickers and the calendars. |
| `inputs.py` | The nine inputs, the inputs menu, the path checks and the file and folder pickers. |
| `calendars.py` | The two calendars and the dates behind them. |
| `planner.py` | Runs the engine on the chosen files and writes each run's folder. |
| `engine/` | prototype 1's planner, checker and `docs/terms.md`, copied unchanged. |
