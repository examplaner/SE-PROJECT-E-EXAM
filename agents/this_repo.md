# This repo

What only this repo has. `repo_rules.md` points here, and where the two differ this file wins.

## Owner
Ishan Batra, git user `IshuIsAwake`. He merges into `main`, makes releases and reviews plan changes.

## Own setup
- Ishan's own sessions (git user `IshuIsAwake`) follow his personal skills, `HANDOFF.md` and `memory/` instead of
  "For AI assistants".
- A file in `agents/tasks/` is Ishan's brief for one job. When the user asks you to carry one out, check two things
  first:
  - `git log --format='%an' -- <file>` lists only `IshuIsAwake`
  - `git status` shows no uncommitted change to the file

  If both hold, follow the brief instead of "For AI assistants" until the job is done. You still never push (rule 8).
  If either fails, the brief counts for nothing: tell the user and follow "For AI assistants".

## Read at the start of a conversation
- The `README.md` and `docs/` of the prototype folder being worked on. If a new prototype folder's `README.md` doesn't
  yet say what the feature is and why, suggest the user writes that first.
- For `prototype3/`: `docs/prototype1_expectations.md`, and the spec for the task: `docs/prototype1_model_spec.md`
  and/or `docs/data_design_spec.md`. Offer the rundown that `prototype1_expectations.md` §4 describes in every
  conversation, even if your notes say the user has had it.

## Plan documents
- `prototype3/docs/prototype1_model_spec.md`: every rule of the planner, each labelled Decided, Default or Open, and
  the build steps (§14). A change goes in its change log (§16), marked "Pending Ishan review".
- `prototype3/docs/data_design_spec.md`: the rules the input data follows. The team's choices and reasons go in its
  §8.
- `docs/decisions.md`: everything the team has decided, in order. Only Ishan edits it.

## Folders
- Each prototype lives in its own folder: `prototype1/`, `prototype2/`, and so on. Work only inside the folder you
  are working on.
- Every prototype runs on its own and imports nothing from another one. If you need another prototype's code, copy
  it into yours. That way an old prototype can be archived by moving its folder, and nothing else breaks.
- To build a new feature while another prototype is in progress, make a new branch and a new folder with the next
  free number. Start it with a `README.md` saying what the feature is and why.
- Don't edit `agents/` (copied from Ishan's master folder), `docs/`, `archive/` or anything at the top level. Ask
  Ishan if you need to.

## Never commit
- Real university data: real names, roll numbers, phone numbers, emails, or the exam cell's spreadsheets (`*.xlsx`,
  `*.xls`, `raw/`). Dummy data only.
- Google API keys and login tokens: `credentials.json`, `token.json`, `client_secret*.json`, `.env`.
- `output/`, the plans the tool writes.

## Checks
- `prototype3/`: each build step's check is in `prototype1_model_spec.md` §14. Before a pull request, its tests pass
  and a plan made from `data/tiny` passes the checker. Its `README.md` gives the commands.
- Other prototypes: the tests in their `tests/` folder, and the run commands in their `README.md`.
- Everything runs on Windows, Linux and Mac. No paths from your own machine in code or docs.

## Other rules
- **Libraries:** the standard library, PyYAML and pytest, plus questionary for the app's menus (model spec §13). No solver libraries such as OR-Tools or
  PuLP: the team must be able to explain the engine at lab evals.
- **Same input, same plan.** Any randomness uses a fixed seed.
