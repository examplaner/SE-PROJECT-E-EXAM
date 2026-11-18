# Exam planner test cases

**191 automated cases passed on 18 November 2026.** The most useful distinction for a demo is *where* a mistake is caught. A misspelled column stops the file reader. An unknown course stops the data validator. A valid three-day exam window can still be too short to schedule everyone. Even after generation, moving one student one seat sideways can make the independent checker reject a saved plan.

[Show both stages live](#show-both-stages-live-in-examplan) · [Recreate five cases](#recreate-five-cases-in-powershell) · [Run the test suites](#run-the-automated-tests) · [Try the interactive CLI](#try-the-interactive-cli) · [Find an individual test](#individual-test-index)

## Run a classroom demonstration in Git Bash

Open Git Bash in the repository folder. Run one command at a time.

```bash
bash prototype2/workflow/tests/run_tests.sh
bash prototype2/workflow/tests/run_tests.sh impossible
bash prototype2/workflow/tests/run_tests.sh all
```

The first command runs three validation examples with the same file checker that the CLI uses. Compare the expected and actual messages for the incorrect header, the unknown course on row 50, and the corrected registration list. Each example prints PASS or FAIL.

The second command runs all seven impossible datasets through the engine. A PASS means the engine returned exit code 2, reported the expected rule and saved the matching explanation as its only output file. The runner prints the explanations on screen and removes the temporary output after the demonstration.

The third command runs all automated cases. Each of the four suites prints its own count. You can also run a group by replacing `all` with `validation`, `schedule`, `seating`, `duties`, `checker` or `workflow`. Both `all` and `--all` run the full suite. [Bash runner](tests/run_tests.sh)

## What is checked and when

| When | What the planner asks | Example you can show |
|---|---|---|
| Selecting inputs in `examplan` | Did the user select a usable path of the right kind? Continue checks the paths again. | Teachers needs a readable, nonempty CSV file. Student lists needs a folder containing CSV files. Cancelling a replacement keeps the previous choice. |
| Input validation, stage 1 | Can the program read the expected files and columns? | A missing file, wrong header, row with the wrong number of values, or malformed YAML gives a file-level error. The folder-based engine finishes these checks before interpreting the records. |
| Input validation, stage 2 | Do the values make sense, and do records in different files agree? | A registration must refer to an existing student and course from the right cohort. A cohort is a program and year. Errors are grouped by rule, with the relevant file and row where available. |
| Before publishing the timetable | Can the exams actually fit the dates, rooms and teacher assignments? | Three exams cannot fit in three calendar days if successive exam dates must be at least two days apart. The interactive planner works out seating and duties before publishing the timetable. |
| After writing the timetable | Does the saved date sheet match the expected papers, slots and student gaps? | The interactive workflow reads the saved schedule back and checks it before announcing success. A second confirmation controls writing seating and duties. |
| After writing the full plan | Do the exported files form a legal plan when read independently? | The output checker reads the timetable, room grids and duty list. It can catch a seating error even when the input files and the timetable are valid. |

The interactive CLI runs stage 1 and the available stage 2 rules after each selection. A relationship is checked as soon as its files are present. Continue rereads all selected inputs before opening the calendars, and generation revalidates the inputs using the confirmed calendar settings. [Menu](interface.py) · [Validation](planner.py)

## Show both stages live in examplan

Start the CLI in PowerShell. The ready-made [Stage 2 registrations file](../../prototype1/data/impossible/registrations_unknown_course.csv) has one extra row. It names an existing student and a course that does not exist.

```powershell
Set-Location 'C:\Users\rs224\Downloads\trial'
examplan
```

1. **Show a stage 1 error.** Highlight **Teachers**, press Enter, and choose `prototype1/data/tiny/rooms.csv`. Both are CSVs, but the program shows `Stage 1 - file structure`, row 1, the expected `teacher_id,rank` header and the room columns it actually read. Press Enter to return. Teachers is still unselected.
2. **Show a pending relationship.** Choose **Student course registrations** before choosing Courses. Pick `prototype1/data/impossible/registrations_unknown_course.csv`. The menu says `Course-code check pending until Courses is selected.`
3. **Trigger stage 2.** Highlight **Courses** and pick `prototype1/data/impossible/window_too_short/courses.csv` (the same course list as tiny). The CLI shows `Stage 2 - data rules` and identifies the unknown course `CSE9999` on row 50. Press Enter or Esc to return to the input menu.
4. **Clear the error.** Replace **Student course registrations** with the original `prototype1/data/tiny/registrations.csv`. The checks available so far now pass. Courses stays selected. Any remaining pending checks name data you still need to supply or indicate that other inputs are needed.
5. **Show the final checkpoint.** Select the remaining inputs from the same `tiny` dataset, including the `sections` folder for student lists. The menu reports that both stages passed. **Continue to exam dates** rereads the files before opening the calendar.

To demonstrate a stage 2 rule with only one file, choose a temporary rooms CSV containing a duplicate room ID. The menu immediately reports the duplicate and its row. A structurally invalid file or a file that fails its own data rules leaves an earlier selection for that item intact. [Live validation tests](tests/test_live_validation.py)

## Recreate five cases in PowerShell

Run the setup **once per PowerShell session**, then run the examples in order. The two bad datasets and the changed plan are copies in a new temporary folder. For a short class demo, cases 1–3 show three distinct outcomes using the same small dataset. Cases 4–5 show why checking the output matters.

```powershell
Set-Location 'C:\Users\rs224\Downloads\trial'
$py = "$env:USERPROFILE\anaconda3\python.exe"
$lab = Join-Path $env:TEMP ("examplan-tests-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $lab | Out-Null
```

`$py` selects the installed Python with the project dependencies. `$lab` gives this run a fresh folder. `$LASTEXITCODE` shows the result of the last Python command. These numeric codes belong to the folder-based engine and checker. The interactive CLI displays errors and offers recovery within the session.

### 1. Break a header to trigger stage 1

Copy the 16-student dataset. Change just the spelling of the first column in `sections.csv`. The rows still contain the original student-section data.

```powershell
$badHeader = Join-Path $lab 'bad-header'
Copy-Item -LiteralPath prototype1/data/tiny -Destination $badHeader -Recurse
$sections = Join-Path $badHeader 'sections.csv'
(Get-Content -LiteralPath $sections) -replace '^section_id,', 'sectoin_id,' |
    Set-Content -LiteralPath $sections -Encoding utf8
& $py -B prototype1/main.py $badHeader --output "$lab/header-out"
$LASTEXITCODE
```

**Expected:** exit `1`. The report names `sections.csv row 1`, shows the expected header and the misspelling, and reports **one problem**. The program stops before checking relationships that depend on that column. [Automated case](../../prototype1/tests/test_validate.py#L74)

### 2. Add a readable row that fails stage 2

Start with a fresh copy. Register an existing student for the made-up course `CSE9999`. The row has exactly the two columns the reader expects.

```powershell
$badCourse = Join-Path $lab 'bad-course'
Copy-Item -LiteralPath prototype1/data/tiny -Destination $badCourse -Recurse
Add-Content -LiteralPath "$badCourse/registrations.csv" -Value 'BT2CSE0001,CSE9999' -Encoding utf8
& $py -B prototype1/main.py $badCourse --output "$lab/course-out"
$LASTEXITCODE
```

**Expected:** exit `1`. The message is `registrations.csv row 50: course code CSE9999 is not in courses.csv`. To explain the difference to your teacher, point out that the program had to read *two files* to know that the row was wrong. [Automated case](../../prototype1/tests/test_validate.py#L98)

### 3. Give valid data with too little time

Use the prepared `window_too_short` dataset. Its window is 2–4 November 2026. A student has three papers, and their exam dates must be at least two days apart.

```powershell
& $py -B prototype1/main.py prototype1/data/impossible/window_too_short --output "$lab/gap"
$LASTEXITCODE
Get-ChildItem -LiteralPath "$lab/gap" -Recurse -Filter why.txt | Get-Content
```

**Expected:** `Input OK`, then `No plan possible.`, `Rule: gap`, and exit `2`. The student can sit exams on 2 and 4 November. Their third paper would need at least 6 November. The run folder contains only `why.txt`, with the same explanation. [Prepared cases](../../prototype1/data/impossible/README.md) · [Tests](../../prototype1/tests/test_no_plan.py)

### 4. Generate a valid plan and check the saved files

```powershell
& $py -B prototype1/main.py prototype1/data/tiny --output "$lab/good"
$plan = (Get-ChildItem -LiteralPath "$lab/good" -Directory | Select-Object -First 1).FullName
& $py -B prototype1/check.py prototype1/data/tiny $plan
$LASTEXITCODE
```

**Expected:** exit `0` and `Plan check: no problems. 7 papers, 7 room files, 48 seats, 14 duties checked.` The 48 occupied seats count **16 students × 3 exams each**. A room file represents one room in one exam session, so the same physical room can have several files over the week. [Automated case](../../prototype1/tests/test_check.py#L79)

### 5. Move one student sideways and run the same checker again

Copy the good plan from case 4. In room S01 on 2 November, move one student taking CSE2001 from column 3 to column 2. Their registration, room and exam time all stay correct. Now the same paper occupies adjacent columns.

```powershell
$changed = Join-Path $lab 'changed-plan'
Copy-Item -LiteralPath $plan -Destination $changed -Recurse
$room = Join-Path $changed 'daywise_seating_plans/2026-11-02/morning/S01.csv'
(Get-Content -LiteralPath $room).Replace('CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007','CSE2001:BT2CSE0001,CSE2001:BT2CSE0007,') |
    Set-Content -LiteralPath $room -Encoding utf8
& $py -B prototype1/check.py prototype1/data/tiny $changed
$LASTEXITCODE
```

**Expected:** exit `3`, one problem under `Rule: column rule`. The report identifies `S01.csv, columns 1 and 2` and paper `CSE2001`. This is a useful answer if your teacher asks, “How do you know the output checker can catch a mistake?” [Automated case](../../prototype1/tests/test_check.py#L106)

## Run the automated tests

From the repository root, with `$py` set as above, run each line separately. The first command uses pytest. The others use Python's built-in unittest runner. The verbose options print the names of individual cases. A test that deliberately supplies bad input **passes** when the planner rejects it in the expected way.

```powershell
& $py -B -m pytest -p no:cacheprovider -v prototype1/tests
& $py -B -m unittest discover -s prototype2/tests -v
& $py -B -m unittest discover -s prototype2/keyboard_cli/tests -v
& $py -B -m unittest discover -s prototype2/workflow/tests -v
```

| Suite | Passed | What the cases exercise |
|---|---:|---|
| [Input validation](../../prototype1/tests/test_validate.py) | 18 | Valid tiny and main data. Missing or damaged inputs. Duplicate IDs, cross-file relationships, room sizes, teacher ranks, dates and shared-paper rules. |
| [Timetable](../../prototype1/tests/test_schedule.py) | 30 | Each course belongs to one scheduled paper. Dates, exam gaps, slot capacity, actual seating and teacher feasibility, repeatability, backup placement strategies, the hand-worked tiny timetable and exported reasons for the chosen strategy. |
| [Seating](../../prototype1/tests/test_seat.py) | 41 | One seat per student per paper, roll order, alternating columns, two-paper limit, room-size choices, joining small leftover groups, teacher eligibility, section boundaries, empty cases and room CSV exports. |
| [Teacher duties](../../prototype1/tests/test_duties.py) | 16 | Required staff per room, avoiding own students, own-paper duty for regular teachers, moving assignments to free a room, undoing failed moves, shift preferences, PhD fallback and shortages. |
| [Impossible plans](../../prototype1/tests/test_no_plan.py) | 12 | Seven prepared datasets, coverage of every failure folder, matching messages in the terminal and file, clean success, and direct checks of boundary conditions. |
| [Independent output checker](../../prototype1/tests/test_check.py) | 28 | Two clean datasets and deliberate damage to dates, seating, duties and file structure. Also covers missing folders, a failure-only folder, and inspection without creating new output. |
| [Numbered input picker](../tests/test_input_selection.py) | 10 | Choosing all inputs, cancel and replacement, invalid paths, empty folder, simulated permission/dialog errors, invalid menu entries, closed terminal and dialog cleanup. |
| [Arrow-key menu](../keyboard_cli/tests/test_menu.py) | 12 | Auto-advance, skipping completed choices, Delete, Cancel, rechecking paths at Continue, Windows key decoding, wrapping and keeping the selection visible in a small terminal. |
| [Interactive workflow](tests/test_workflow.py) | 16 | Six calendar cases, five workflow navigation/retry cases and five generation cases. The generation group exercises the engine with actual dummy files and reads the exports. |
| [Live input validation](tests/test_live_validation.py) | 8 | Checks while picking, cross-file errors in either order, correction, pending checks and rereading inputs. |
| **Total** | **191** | **145 engine cases and 46 interface/workflow cases.** |

Counts are test runs. For example, the same test can run once on `tiny` and once on `main`. The 145 engine tests target prototype 1. The interactive workflow's copy of the validator also supports partially selected inputs. The earlier menu suites exercise their respective interfaces. The workflow suite runs 24 cases, including eight for live validation. Archived experiments and the separate visual calendar script are outside the total.

### Run just the case your teacher asks about

```powershell
& $py -B -m pytest -q prototype1/tests/test_validate.py::test_unknown_course_code_names_the_row
& $py -B -m pytest -q prototype1/tests/test_schedule.py::test_tiny_schedule_worked_out_by_hand
& $py -B -m pytest -q prototype1/tests/test_seat.py::test_45_students_get_one_m_and_two_s_rooms_with_no_empty_seat
& $py -B -m pytest -q prototype1/tests/test_duties.py::test_chain_of_moves_finds_a_place
& $py -B -m pytest -q prototype1/tests/test_check.py::test_column_rule
& $py -B -m unittest discover -s prototype2/workflow/tests -k test_full_main_seating_passes_independent_checker -v
```

Each command above runs one test. In the room-choice example, one medium room holds 21 students taking one paper and each small room holds 12. The expected choice seats all 45 in three rooms. In the duty example three teachers have overlapping room choices. Moving two earlier assignments lets the third teacher take a legal room. Both are more informative than simply showing that a file was produced.

## Seven prepared ways a plan can fail

Each folder is under `prototype1/data/impossible/`. To reproduce another case, use the command in case 3 and replace `window_too_short` with the folder name. Each dataset passes input validation, returns exit `2` and creates a fresh folder containing only `why.txt`. [Dataset notes](../../prototype1/data/impossible/README.md)

| Folder | What to explain | Expected rule |
|---|---|---|
| `no_exam_days` | Only Saturdays are allowed, but the entire window is Monday to Friday. | `exam days` |
| `window_too_short` | Each student needs three papers. Only two fit at the required gap. | `gap` |
| `paper_too_big` | One paper has 16 students. The only room seats 12 for a single paper when alternate columns are used. | `seats` |
| `no_day_fits` | A paper needs two rooms with five invigilators each. Only nine teachers exist. | `paper placement` |
| `waiting_paper` | T005 teaches every student taking the shared paper. No other paper can share its slot to provide an eligible room. | `duty room` |
| `duty_room_full` | T005 and T006 both need the same eligible room. It has one duty place. | `duty room` |
| `too_few_teachers` | The slot needs all nine teachers. One has their own students in every available room, so eight eligible teachers cannot cover nine duties. | `duties` |

## Other checks worth explaining

### Data rules after the files can be read

- Each student belongs to exactly one section. Each section needs its roster. Duplicate IDs and duplicate registrations are reported.
- Every student needs a registration, every course needs a student, and each registration must match the student's cohort. A teaching assignment must name an existing teacher, course and section with students actually taking that course.
- Room dimensions must be positive whole numbers, room types and teacher ranks must be recognized, and the start date must precede or equal the end date. Settings require two distinct sessions and positive whole numbers for the exam gap and invigilators per room.
- A shared paper groups two or more known course codes. A code appearing twice or in two groups is reported. Multiple errors of one kind appear together with a count and individual details. [Validator](../../prototype1/validate.py) · [Validation tests](../../prototype1/tests/test_validate.py)

### Hard rules and scheduling preferences

A hard rule can invalidate a plan. For example, a teacher cannot supervise their own students or cover two rooms in one slot. A preference helps pick between legal plans. Examples include keeping one paper per room when possible, using regular teachers before PhD scholars, and avoiding a second shift on the same day when possible. These preferences have generation tests. The independent checker verifies the yes/no rules of the saved plan. It does not certify a globally optimal timetable.

The timetable tests also exercise three placement strategies. The first prefers the slot that adds the fewest rooms, breaking ties by fewer students. The second uses an earlier-day tie-break. The third tries earliest feasible placement. Tests force failures to verify that fallback works and that the selected approach is recorded in `basis.txt`. [Timetable tests](../../prototype1/tests/test_schedule.py) · [Duty tests](../../prototype1/tests/test_duties.py)

### The output checker itself has three stages

1. **File structure.** Can the saved files be read? Does each room grid have the right dimensions, and are its cells readable? A missing duties file or malformed room grid stops further checks.
2. **Individual records.** Is this paper scheduled in this slot? Is this student registered for it? Is this duty assigned to a known teacher in a room actually being used? An invalid row is reported and excluded from dependent checks.
3. **Rules across records.** Does each student get exactly one seat per paper and the required exam gap? Do columns, roll order, room staffing, one duty per teacher per slot, and teacher eligibility all hold? Case 5 is a stage 3 failure.

The checker reads saved files using its own reading and checking code. A generator and a checker that shared the same mistaken seat-placement logic could both accept the same wrong result. The deliberate damage in case 5 demonstrates what independent checking contributes. [Checker stages and rule list](../../prototype1/check.py) · [Checker tests](../../prototype1/tests/test_check.py)

## Try the interactive CLI

Open an interactive Windows terminal and type `examplan`. These are manual demonstrations. Picker and workflow navigation tests use simulated choices for repeatability. Real generation tests write and check actual plans in temporary folders.

| Try this | What you should see |
|---|---|
| Select `prototype1/data/main/teachers.csv`. Go back to Teachers, reopen the picker and press Cancel. | Teachers still shows the original filename. A successful selection moves to the next missing input. |
| Highlight Teachers and press Delete. Then choose Continue with Teachers missing. | Only that selection clears. The original CSV still exists. Continue highlights the missing item. |
| Fill all nine choices from `prototype1/data/main`. Use `sections.csv` for section information and the `sections` folder for student lists. Continue to the calendars. | The range and excluded dates appear in separate windows. With the original settings, Saturday 7 November and the holiday on 11 November 2026 are excluded. Tuesday 10 November is available. |
| Confirm the original range and exclusions. Choose **No** at the timetable question. | The input menu returns with the file choices still present. |
| Use the main data with the range 2–4 November 2026, retain the default exclusions and confirm generation. Extend the range back to 20 November when prompted. | The short range gives a gap explanation and a path to `why.txt`. The workflow returns to the range calendar and retains the input files for another attempt. |
| Using the original main settings, choose **Yes** for the timetable, then **No** for seating. | The timetable path has been reported. Its schedule is saved, and the input menu returns. Seating and duty files require the second confirmation. |
| Run with the original main settings and confirm both outputs. | The checker reports **56 papers, 454 room files, 8,750 occupied seats across exams and 908 duty assignments**. The terminal gives paths for the plan and duties. A repeat export gets a fresh folder. |

The calendar suite additionally checks a one-day window on leap day, a reversed range, a click outside the range, a one-run weekend exception, and retaining exclusions when shrinking and re-extending the range. There is a separate [visual calendar check](tests/check_calendar_windows.py) with saved [range](review/range.png) and [exclusion](review/holidays.png) previews. Its script expects to create a new preview directory, so use the CLI walkthrough to demonstrate the calendars in this checkout.

### Implemented protections and their evidence

- **Source files stay intact.** The generation tests compare content fingerprints before and after running. A fingerprint is a value calculated from the file's bytes, so a content change can be detected. The workflow records source paths and fingerprints in `sources.json` and saves the effective settings alongside the output.
- **Input changes during generation.** The workflow compares fingerprints again before creating the result folder. The suite checks that normal generation leaves the inputs intact. There is no dedicated named case in the active suites that changes a file during generation.
- **Protection against unusable or incomplete exports.** Room IDs and session names are checked for Windows filename restrictions. The export error handlers write `INCOMPLETE.txt` for failures inside their guarded write/check blocks. These checks are implemented. The active suites do not explicitly inject those two failures.
- **Fresh output directories.** The workflow test exports seating twice and asserts that the directories differ. A separate short-window test verifies that a planning failure writes only the original explanation to `why.txt`. [Implementation](planner.py) · [Generation tests](tests/test_workflow.py)

## Individual test index

Expand a suite to see every collected case. Run an individual case from the repository root using the command pattern shown in its section. Brackets identify a specific dataset used by a test. Counts include those separate runs.

<details>
<summary>prototype2/workflow/tests/test_live_validation.py (8 cases)</summary>

```powershell
& $py -B -m pytest -q prototype2/workflow/tests/test_live_validation.py
```

- `LiveValidationTests::test_bad_header_keeps_previous_selection`
- `LiveValidationTests::test_duplicate_room_rejected_with_just_rooms`
- `LiveValidationTests::test_unknown_course_in_either_order_and_replacement`
- `LiveValidationTests::test_continue_rereads_files_before_calendar`
- `LiveValidationTests::test_every_prefix_of_valid_selection_can_continue_when_complete`
- `LiveValidationTests::test_empty_course_catalog_counts_as_selected`
- `LiveValidationTests::test_roster_and_shared_paper_checks_run_when_dependencies_arrive`
- `LiveValidationTests::test_generation_rechecks_source_settings_after_calendar`

</details>

<details>
<summary>prototype1/tests/test_check.py (28 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype1/tests/test_check.py::test_clean_tiny_plan"
```

- `test_clean_tiny_plan`
- `test_clean_main_plan`
- `test_checker_writes_nothing`
- `test_column_rule`
- `test_wrong_paper_in_a_cell_is_one_problem`
- `test_student_not_in_input`
- `test_student_seated_twice`
- `test_student_with_no_seat`
- `test_roll_order`
- `test_one_paper_per_column`
- `test_gap_rule`
- `test_exam_on_a_holiday`
- `test_same_paper_codes`
- `test_date_moved_in_schedule_only`
- `test_room_short_of_a_teacher`
- `test_teacher_in_two_rooms`
- `test_teacher_with_own_students`
- `test_teacher_without_own_paper_duty`
- `test_duty_in_an_unused_room`
- `test_unknown_teacher`
- `test_room_csv_with_a_row_missing`
- `test_bad_cell`
- `test_extra_file_in_plan_folder`
- `test_missing_duties_csv`
- `test_no_plan_folder_gives_exit_2`
- `test_missing_input_folder_gives_exit_1`
- `test_missing_rooms_csv_gives_exit_1`
- `test_missing_plan_folder_gives_exit_1`

</details>

<details>
<summary>prototype1/tests/test_duties.py (16 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype1/tests/test_duties.py::test_first_choice_is_a_room_with_the_paper_but_none_of_own_students"
```

- `test_first_choice_is_a_room_with_the_paper_but_none_of_own_students`
- `test_otherwise_a_room_with_a_different_paper`
- `test_never_a_room_with_own_students_of_any_paper`
- `test_teachers_without_room_lists_them_and_skips_phd_scholars`
- `test_own_paper_duty_comes_first`
- `test_chain_of_moves_finds_a_place`
- `test_chain_that_fails_changes_nothing`
- `test_phd_scholars_only_when_no_regular_teacher_is_free`
- `test_second_shift_on_a_day_comes_after_fewest_duties`
- `test_evening_goes_to_someone_free_that_day`
- `test_no_plan_when_teachers_run_out`
- `test_no_plan_when_own_paper_rooms_are_full`
- `test_no_plan_when_two_own_papers_need_different_rooms`
- `test_every_rule_holds_on_real_data[tiny]`
- `test_every_rule_holds_on_real_data[main]`
- `test_main_writes_duties_csv`

</details>

<details>
<summary>prototype1/tests/test_no_plan.py (12 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype1/tests/test_no_plan.py::test_every_impossible_folder_has_a_test"
```

- `test_every_impossible_folder_has_a_test`
- `test_impossible_dataset_says_why[duty_room_full]`
- `test_impossible_dataset_says_why[no_day_fits]`
- `test_impossible_dataset_says_why[no_exam_days]`
- `test_impossible_dataset_says_why[paper_too_big]`
- `test_impossible_dataset_says_why[too_few_teachers]`
- `test_impossible_dataset_says_why[waiting_paper]`
- `test_impossible_dataset_says_why[window_too_short]`
- `test_valid_input_writes_no_why_txt`
- `test_most_papers_in_window`
- `test_cheap_checks_pass_when_everything_fits`
- `test_backup_one_own_paper_with_no_room`

</details>

<details>
<summary>prototype1/tests/test_schedule.py (30 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype1/tests/test_schedule.py::test_every_course_code_is_in_exactly_one_paper_and_slot[tiny]"
```

- `test_every_course_code_is_in_exactly_one_paper_and_slot[tiny]`
- `test_every_course_code_is_in_exactly_one_paper_and_slot[main]`
- `test_gap_rule_for_every_student[tiny]`
- `test_gap_rule_for_every_student[main]`
- `test_only_exam_days_are_used[tiny]`
- `test_only_exam_days_are_used[main]`
- `test_no_session_goes_over_the_seat_limit[tiny]`
- `test_no_session_goes_over_the_seat_limit[main]`
- `test_same_input_gives_same_plan`
- `test_seat_limit_of_rooms`
- `test_exam_days_skip_weekends_and_holidays`
- `test_tiny_schedule_worked_out_by_hand`
- `test_main_writes_schedule_csv`
- `test_window_too_short_for_the_gap_rule`
- `test_not_enough_seats`
- `test_not_enough_teachers`
- `test_a_session_must_really_be_seatable_not_just_counted`
- `test_a_paper_goes_where_it_adds_the_fewest_rooms`
- `test_the_old_way_still_takes_the_earliest_day`
- `test_tie_in_rooms_fewer_students_or_earlier_day`
- `test_session_check_gives_the_problem_and_the_room_count`
- `test_the_first_way_works_on_tiny_and_the_basis_says_so`
- `test_main_falls_back_to_the_next_way_and_says_so`
- `test_two_ways_fail_then_the_old_way_makes_the_plan`
- `test_no_plan_only_when_the_last_way_fails_too`
- `test_main_writes_basis_txt_and_prints_the_same_two_lines`
- `test_every_plan_folder_gets_terms_md`
- `test_every_teacher_has_a_room_for_each_paper_they_teach[tiny]`
- `test_every_teacher_has_a_room_for_each_paper_they_teach[main]`
- `test_a_slot_still_waiting_at_the_end_is_no_plan`

</details>

<details>
<summary>prototype1/tests/test_seat.py (41 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype1/tests/test_seat.py::test_one_paper_per_room_best_room_sizes"
```

- `test_one_paper_per_room_best_room_sizes`
- `test_leftovers_are_mixed_when_rooms_run_out`
- `test_mixing_only_where_needed`
- `test_a_room_never_holds_a_third_paper`
- `test_one_paper_alone_uses_every_other_column`
- `test_tie_in_size_goes_by_paper_id`
- `test_only_rooms_in_use_are_returned`
- `test_every_student_gets_exactly_one_seat_per_paper[tiny]`
- `test_every_student_gets_exactly_one_seat_per_paper[main]`
- `test_column_rule_and_at_most_two_papers_per_room[tiny]`
- `test_column_rule_and_at_most_two_papers_per_room[main]`
- `test_a_shared_room_holds_only_the_last_students_of_two_papers[tiny]`
- `test_a_shared_room_holds_only_the_last_students_of_two_papers[main]`
- `test_students_sit_in_roll_order[tiny]`
- `test_students_sit_in_roll_order[main]`
- `test_a_room_is_used_once_per_slot[tiny]`
- `test_a_room_is_used_once_per_slot[main]`
- `test_same_input_gives_same_seating`
- `test_main_writes_one_csv_per_room_in_use`
- `test_each_section_starts_a_new_room_when_it_costs_no_extra_room`
- `test_sections_stay_together_when_a_new_room_would_cost_a_room`
- `test_45_students_get_one_m_and_two_s_rooms_with_no_empty_seat`
- `test_a_few_leftover_students_do_not_get_a_big_room`
- `test_fewest_rooms_come_before_fewest_empty_seats`
- `test_papers_share_the_rooms_of_the_slot`
- `test_roll_order_kept_across_the_chosen_rooms`
- `test_a_teacher_with_no_room_makes_the_paper_split_by_section`
- `test_old_way_is_the_backup_when_the_teacher_check_still_fails`
- `test_room_options_never_have_a_spare_room`
- `test_no_rooms_means_no_best_way`
- `test_two_leftovers_share_one_room`
- `test_the_pair_that_fills_the_room_best_is_joined_first`
- `test_in_an_s_room_the_bigger_leftover_takes_the_two_odd_columns`
- `test_full_rooms_are_never_joined`
- `test_a_leftover_with_no_partner_stays_alone`
- `test_one_paper_alone_in_a_slot_is_never_joined_with_itself`
- `test_a_joined_room_never_gets_a_third_paper`
- `test_no_join_when_a_teacher_would_have_no_room`
- `test_no_join_that_would_break_roll_order`
- `test_join_leftovers_with_no_rooms_or_plans`
- `test_basis_line_when_every_room_holds_one_paper`

</details>

<details>
<summary>prototype1/tests/test_validate.py (18 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype1/tests/test_validate.py::test_generated_datasets_are_valid[tiny]"
```

- `test_generated_datasets_are_valid[tiny]`
- `test_generated_datasets_are_valid[main]`
- `test_missing_input_folder`
- `test_missing_file`
- `test_bad_header_gives_one_error_not_a_flood`
- `test_row_with_too_few_values`
- `test_broken_yaml`
- `test_unknown_course_code_names_the_row`
- `test_errors_are_grouped_with_a_count`
- `test_duplicate_id`
- `test_student_in_two_sections`
- `test_student_with_no_registrations`
- `test_registration_for_another_cohort`
- `test_course_with_no_students`
- `test_teaching_a_section_with_no_students_for_it`
- `test_bad_room_and_rank_values`
- `test_bad_settings`
- `test_bad_constraints`

</details>

<details>
<summary>prototype2/tests/test_input_selection.py (10 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype2/tests/test_input_selection.py::InputSelectionTests::test_cancel_first_picker_does_not_exit"
```

- `InputSelectionTests::test_cancel_first_picker_does_not_exit`
- `InputSelectionTests::test_cancel_replacement_keeps_previous_and_other_choices`
- `InputSelectionTests::test_closed_terminal_exits_cleanly`
- `InputSelectionTests::test_empty_folder_and_permission_error`
- `InputSelectionTests::test_invalid_menu_entries_do_not_open_picker`
- `InputSelectionTests::test_invalid_replacement_keeps_original`
- `InputSelectionTests::test_path_checks_reject_wrong_kind_and_missing_path`
- `InputSelectionTests::test_picker_failure_and_interrupt_preserve_choices`
- `InputSelectionTests::test_picker_uses_file_or_folder_dialog_and_destroys_window`
- `InputSelectionTests::test_select_all_existing_main_inputs`

</details>

<details>
<summary>prototype2/keyboard_cli/tests/test_menu.py (12 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype2/keyboard_cli/tests/test_menu.py::MenuTests::test_cancel_replacement_keeps_highlight_and_all_choices"
```

- `MenuTests::test_cancel_replacement_keeps_highlight_and_all_choices`
- `MenuTests::test_continue_focuses_first_missing_input`
- `MenuTests::test_continue_rechecks_paths_that_changed_since_selection`
- `MenuTests::test_delete_continue_is_not_an_exit_or_bulk_clear`
- `MenuTests::test_delete_only_clears_highlighted_choice_and_does_not_move`
- `MenuTests::test_exit_and_wrapped_navigation`
- `MenuTests::test_invalid_replacement_does_not_discard_old_selection`
- `MenuTests::test_picker_error_and_back_keep_previous_choices`
- `MenuTests::test_replacement_advances_past_already_selected_input`
- `MenuTests::test_small_terminal_keeps_highlighted_exit_visible`
- `MenuTests::test_success_advances_through_all_inputs_to_continue`
- `MenuTests::test_windows_extended_keys_are_decoded`

</details>

<details>
<summary>prototype2/workflow/tests/test_workflow.py (16 cases)</summary>

Run one case by replacing the quoted test identifier below with any identifier from this list.

```powershell
& $py -B -m pytest -q "prototype2/workflow/tests/test_workflow.py::CalendarTests::test_extend_range_keeps_overrides_and_applies_existing_weekdays"
```

- `CalendarTests::test_extend_range_keeps_overrides_and_applies_existing_weekdays`
- `CalendarTests::test_file_weekdays_and_holiday_are_preselected`
- `CalendarTests::test_invalid_range_and_outside_click`
- `CalendarTests::test_leap_year_and_single_day_range`
- `CalendarTests::test_shrinking_then_extending_range_preserves_prior_choices`
- `CalendarTests::test_weekend_can_be_allowed_for_this_run_only`
- `FlowTests::test_calendar_back_preserves_inputs_and_calendar`
- `FlowTests::test_gap_failure_returns_to_calendar_then_retry_uses_extended_range`
- `FlowTests::test_no_seating_preserves_timetable_and_returns_to_selection`
- `FlowTests::test_no_timetable_goes_back_without_losing_inputs`
- `FlowTests::test_other_failure_allows_input_recovery`
- `GenerationTests::test_all_original_inputs_remain_unchanged`
- `GenerationTests::test_failure_is_existing_engine_message_and_only_why_is_written`
- `GenerationTests::test_full_main_seating_passes_independent_checker`
- `GenerationTests::test_main_timetable_is_written_without_seating_files`
- `GenerationTests::test_missing_course_file_is_reported_without_creating_output`

</details>
