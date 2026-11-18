# Start here

## Latest session — 2026-11-17

Current branch is now `krish/cli`, created from `krish/fixes2` at Krish's explicit request. No CLI implementation, commit or push. Existing untracked `data/demo/` is untouched. The older state below describes the inherited engine.

Krish wants a terminal interface to supply exam data, enter the exam window, and skip selected dates. Review found that the engine already supports dates, weekdays and holidays in `settings.yaml`. Proposed next increment is a guided wizard in a new `prototype2/`, copying the existing engine as required by repo rules. Keep the effective input/settings available for the independent checker. Input selection (one folder versus separate paths), file formats (CSV versus Excel), and settings persistence still need answers and approval before code.

Tests are not reverified: the WindowsApps `python` launcher cannot run here; an existing Python was found at `C:/Users/rs224/AppData/Roaming/uv/python/cpython-3.14-windows-x86_64-none/python.exe`, but it has no `pytest`. No dependencies were installed. Historical baseline: 145 passing tests. See the new review entry in `PROGRESS.md`.

Exact next step: get Krish's workflow decisions and approval for the first reviewable CLI step, then implement only that step and ask for its concrete user check. Read `repo_instructions.md` first. The README purpose for the new prototype must use the human's description of the feature and why it is needed.

## Previous engine handoff

**Current state:** on branch `krish/fixes2` (from `krish/fixes1`, made 2026-11-10). Fix 2 (join the leftovers) is committed on `krish/fixes1`. Fix 3 (sessions chosen by fewest rooms, 2026-11-10) is done, checked by Krish and committed on `krish/fixes2`: `schedule.make_schedule()` tries three ways in order (fewest rooms with tie fewer students; fewest rooms with tie earlier day; the old earliest day) and `main.py` prints two basis lines (on what basis the timetable and the seating were made) and writes them to `basis.txt` in the plan folder; the timetable line names any way that failed first. A third line points to `terms.md`, a copy of `docs/terms.md` (what the words of the plan mean) in every plan folder. `main`: 454 rooms (was 494, and 510 before Fix 2), 908 duties, 105 both-shift teacher-days; the first way can't place ECE2003, so the second way makes the schedule. 145 tests pass (about 1.5 minutes); `check.py` is clean on `tiny` and `main`. Details in `PROGRESS.md` (Fix 2, Fix 3) and spec §8, §9, §11 (2026-11-10 rows). Nothing is pushed by Claude; Krish pushes.

**Open problems:** Krish hasn't said whether rooms that are nearly full alone should be left out of joining (still joined). The four 2026-11-10 change log rows and the earlier rows of 2026-10-22, 2026-10-28, 2026-11-03 and 2026-11-09 are pending Ishan. One shift a day per teacher still doesn't fit `main` (but both-shift days fell from 316 to 105). `krish/generator`, `krish/load-validate`, `krish/schedule`, `krish/seat`, `krish/duties`, `krish/checker`, `krish/wrap-up`, `krish/fixes`, `krish/fixes1`, `krish/fixes2` still need PRs into `main`. `data/demo/` is an untracked copy of `tiny`. Step 7 open point: "two own papers, no one room for both" can still reach step 6 (it stops there with no plan, so never a bad plan).

**Git in this folder from a Linux shell:** use `git -c core.autocrlf=true ...`, or every file shows as changed. Committing needs delete permission (git removes its lock files). Author: Krish Sharma <krish425988888@gmail.com> (the Linux shell has no git identity: pass `-c user.name=... -c user.email=...`).

**Tests from a Linux shell:** pytest was installed there with `pip install --user --break-system-packages pytest` (2026-11-05, outside the repo). On Krish's machine, `python -m pytest tests` works as usual.

**Exact next step:** Krish skims `docs/terms.md` (copied into every plan folder as `terms.md`) before pushing, then pushes `krish/fixes1` and `krish/fixes2` (`git push -u origin krish/fixes1`, `git push -u origin krish/fixes2`). Then PRs into `main`, or the next fix.
