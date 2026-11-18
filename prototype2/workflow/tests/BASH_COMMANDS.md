# Bash test commands

Open **Git Bash** in the repository folder:

```bash
cd /c/Users/rs224/Downloads/trial
```

Run one command at a time. Each command starts with the common runner.

## Classroom demos

```bash
bash prototype2/workflow/tests/run_tests.sh
bash prototype2/workflow/tests/run_tests.sh demo
bash prototype2/workflow/tests/run_tests.sh impossible
```

- No argument or `demo` shows the Stage 1 wrong-header message, the Stage 2 unknown-course message on row 50, and the corrected file passing.
- `impossible` runs all seven prepared impossible datasets. Each prints its reason and reports whether the expected rule and `why.txt` match.

## Run one test group

```bash
bash prototype2/workflow/tests/run_tests.sh validation
bash prototype2/workflow/tests/run_tests.sh schedule
bash prototype2/workflow/tests/run_tests.sh seating
bash prototype2/workflow/tests/run_tests.sh duties
bash prototype2/workflow/tests/run_tests.sh no-plan
bash prototype2/workflow/tests/run_tests.sh checker
bash prototype2/workflow/tests/run_tests.sh workflow
```

- `validation` checks the input data rules and live CLI validation.
- `schedule` checks timetable creation, exam days, gaps and room capacity.
- `seating` checks student seats, room use, paper spacing and seating order.
- `duties` checks teacher-room assignments and staffing rules.
- `no-plan` runs the step 7 automated tests for failure messages, output, and backup feasibility checks. Use `impossible` separately to demonstrate all seven prepared input datasets.
- `checker` checks that invalid or damaged saved plans are detected.
- `workflow` checks calendars, menu navigation, generation, retries and output export.

## Run every automated test

```bash
bash prototype2/workflow/tests/run_tests.sh all
bash prototype2/workflow/tests/run_tests.sh --all
```

Both commands run all four test folders: prototype 1, prototype 2 input selection, the arrow-key menu, and the interactive workflow. The runner starts a fresh test process for each folder because prototype 1 and prototype 2 contain modules with the same names.

## Show the runner help

```bash
bash prototype2/workflow/tests/run_tests.sh --help
```

See [TEST_CASES.md](../TEST_CASES.md) for what the tests check and expected results.

## Match the commands to the recorded prototype steps

The stage and test names are recorded in [prototype1/PROGRESS.md](../../../prototype1/PROGRESS.md).

| Recorded work | Command |
|---|---|
| Step 3, load and validate | `bash prototype2/workflow/tests/run_tests.sh validation` |
| Step 4, schedule | `bash prototype2/workflow/tests/run_tests.sh schedule` |
| Step 5, seat | `bash prototype2/workflow/tests/run_tests.sh seating` |
| Step 6, duties | `bash prototype2/workflow/tests/run_tests.sh duties` |
| Step 7, no plan | `bash prototype2/workflow/tests/run_tests.sh no-plan` |
| Step 8, independent checker | `bash prototype2/workflow/tests/run_tests.sh checker` |
| Interactive input, keyboard menu and workflow | `bash prototype2/workflow/tests/run_tests.sh workflow` |

Step 2's data generator has no dedicated automated test module in the current suites. Its output datasets are checked by the validation tests. The seven folders under `prototype1/data/impossible` are sample data for Step 7, while `no-plan` runs the automated tests for that step.
