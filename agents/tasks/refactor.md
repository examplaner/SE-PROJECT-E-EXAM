# Brief: refactor prototype1 and prototype2

Written by Ishan (`IshuIsAwake`) for one job. Check that it counts before following it: `agents/this_repo.md`, "Own
setup".

## The job
prototype1 and prototype2 work, but the code is far longer and harder to explain than it needs to be. Rewrite it so
that it does the same thing with simpler code. Keep the behaviour, change the code. The two are independent of each other, so its fine if some code is copied. 

The plan is fixed in the specs, not here. Read `agents/repo_rules.md`, `agents/this_repo.md`,
`prototype1/docs/prototype1_model_spec.md` and `prototype1/docs/data_design_spec.md` first.

## How to work
- The user running you is a friend helping Ishan out, not on the team. He accepts your plan and then leaves you
  running. Work end to end on your own judgement. Don't stop to ask and don't wait for confirmations after the plan.
  Where something is unclear, pick the option that keeps the behaviour, write the choice in the report and carry on.
- Follow `agents/skills/code/SKILL.md`. Write the plan first, in plan mode. The plan names the new modules and
  functions of each prototype, and the order of the work.
- Work on a branch named `abhishek/refactor`, made from `main`. Commit after each finished piece. Commit messages
  say what changed and why. Never push: when you are done, give the user the push command.
- Keep `REFACTOR_REPORT.md` at the top of the repo up to date as you go. It is where you pick up after a long break
  or a compacted context.
- Don't touch `agents/`, `docs/`, `archive/` or any top-level file other than `REFACTOR_REPORT.md`.

## What the code must look like
- `agents/repo_rules.md` §7 and the code skill. A third-year student can explain every line after one read.
- Remove repeated code inside a prototype. Each prototype stays independent, so prototype2 keeps its own full copy of
  the engine (`agents/this_repo.md`, "Folders").
- Module docstrings that tell the history ("redone 2026-11-03, Krish's decision ...") go. A reason that still matters
  becomes a one or two line comment. The history stays in the spec change logs and in git.
- Runs on Windows, Linux and Mac, from any folder: `pathlib`, `encoding="utf-8"` on every file, no paths from one
  machine, no Windows-only modules. Each prototype gets a `requirements.txt` with pinned versions.
- Libraries: the standard library, PyYAML and pytest. prototype2 also gets `questionary` for arrow-key menus and
  yes/no prompts (Ishan approved it). Nothing else.
- Shorter might be a result, not the goal. Never squeeze lines together to save space. What is important that the code is explainable and only what is required is there - using the skill - code in agents is important.

## prototype1
- The engine (`main.py`, `loader.py`, `validate.py`, `schedule.py`, `seat.py`, `duties.py`, `errors.py`), the checker
  (`check.py`) and the generator (`tools/generate_data.py`).
- Same command line, same input folder, same output folder layout, same exit codes.
- The checker still imports nothing from the engine, so a bug in the engine can't hide from it.
- Don't change any file under `data/`. The new generator must write exactly the files that are there now.

## prototype2
- `workflow/` is the app. `input_selection.py` and `keyboard_cli/` were earlier steps of it. Make them one app with
  one entry point.
- Keep every behaviour that `workflow/README.md` and `keyboard_cli/README.md` describe:
  - inputs are chosen with Tkinter file and folder pickers, never by typing a path
  - arrow keys and Enter move and choose; after a choice, the menu moves to the next missing input; Delete clears a
    choice without touching its file; Cancel in a picker keeps the old choice
  - the exam range and the no-exam days are chosen in Tkinter calendars, with the settings' weekdays and holidays
    already marked
  - the app asks before making the timetable, and again before writing the seating plan
  - a failure shows the engine's reason and lets the user change dates or inputs without starting over
  - every run writes a new output folder; nothing is overwritten and input files are never written
- `msvcrt` and `ctypes` go. Menus and yes/no prompts use `questionary`.
- Its engine folder is an exact copy of prototype1's refactored engine and checker.
- It gets its own copy of the datasets it needs, so it still runs if `prototype1/` is archived.

## Tests
There are two kinds, kept in separate folders.

- **Code tests** (`tests/unit/` in each prototype, pytest): you write these. They test the code and the behaviour.
  The old tests show what to cover. Cover the same behaviour through the new functions, without near-duplicates, then
  delete the old tests. They stay readable at the `pre-refactor` tag.
- **Demo cases** (`prototype1/tests/demo/`, bash): Himank's 10 cases from `prototype2/workflow/tests/demo/`. They are
  the team's own tests, presented at lab evals. They run the engine and the checker from outside and check exit
  codes and messages, so they must pass before and after the refactor.
  - Move them to prototype1 and point them at prototype1's `main.py` and `check.py`.
  - Make them the most explainable code in the repo. Each case reads top to bottom. A comment above each step says
    what it does and why, so Himank can explain every line. Comments are welcome here.
  - Keep what each case checks.
  - They run in Git Bash on Windows and in bash on Linux and Mac.
- `setup.ps1`, `requirements-demo.txt` and `check_calendar_windows.py` are Windows only. Replace them with setup and
  run steps in each prototype's `README.md` that work on all three systems.

## Proving the behaviour stayed the same
1. Before changing any code, check out the tag `pre-refactor` into a folder outside the repo, for example with
   `git worktree add ../pre-refactor pre-refactor`. That is the old copy.
2. Run the old prototype1 on `data/tiny`, `data/main` and every folder in `data/impossible/`. Keep the exit code,
   the printed output and the output folder of each run.
3. After each piece of work, run the new code the same way and compare: exit code, printed output and every file in
   the output folder. Ignore only the timestamp in the folder name.
4. The old `check.py` passes every new plan, and the new `check.py` passes every old plan.
5. Broken plans and broken inputs: build the ones the old `test_check.py`, `test_validate.py` and the demo cases
   build. The old and new code give the same exit code and name the same rule.
6. The new generator writes the same files as `data/`, byte for byte.
7. prototype2: its planning, without the menus and calendars, gives the same plan as prototype1 for the same input.
   The menus and calendars need a person: write the steps to try them by hand in the report.

A difference with no good reason is a bug: fix it. A difference with a good reason, such as a real bug fixed or a
message made clearer, stays: write it in the report with the reason. If it changes a rule in a spec, also add a row
to that spec's change log marked "Pending Ishan review".

## Docs
- Delete every `PROGRESS.md` and `handoff.md` in prototype1 and prototype2. They are AI notes (rule 6).
- Each prototype's `README.md`: short and plain. What it does, how to set it up and run it on Windows, Linux and Mac,
  and what comes out.
- `prototype1/docs/terms.md` is copied into every plan folder, so it stays.
- In the specs, change only names of files or functions that no longer exist. Leave the "Pending" rows in the change
  logs as they are: Ishan reviews them.

## Handing over
`REFACTOR_REPORT.md` ends up with:
- the plan as accepted
- lines of code before and after, per file
- the result of each comparison step above, per dataset
- every difference and its reason
- bugs found, fixed or not
- what wasn't checked, and the steps to try prototype2 by hand

Then give the user: `git push -u origin abhishek/refactor`.
