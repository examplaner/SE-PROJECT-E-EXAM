"""The checker (check.py). Each test makes a fresh plan from the small dataset
with main.py, breaks one thing by hand, and checks that the checker finds it
and shows only the main issue, not a flood of follow-on errors.

The plan these tests break (main.py always makes the same one):

    2026-11-02 morning  CSE2001 (with CSE2003)
                        S01: BT2CSE0001-0008    duties T001, T003
                        S02: BT2ECOM0001-0008   duties T002, T005
    2026-11-04 morning  CSE2002 in S01, ECE2001 in S02
    2026-11-06 morning  MTH2001 + PHY2002 in S01, BIO2001 in S02,
                        PHY2001 in M01
"""

import shutil
from pathlib import Path

import pytest

import check
from conftest import IMPOSSIBLE_DATASETS, REALISTIC_DATASET, SMALL_DATASET, replace_once, run_main

ROOMS_2_NOV = Path("daywise_seating_plans") / "2026-11-02" / "morning"
S01_2_NOV = ROOMS_2_NOV / "S01.csv"
S02_2_NOV = ROOMS_2_NOV / "S02.csv"
S01_6_NOV = Path("daywise_seating_plans") / "2026-11-06" / "morning" / "S01.csv"


def make_plan(tmp_path, capsys, dataset=SMALL_DATASET):
    code, printed, folder = run_main(dataset, tmp_path / "out", capsys)
    assert code in (0, 2), printed
    return folder


def run_check(input_dir, plan, capsys):
    """Returns (exit code, printed text)."""
    code = check.main([str(input_dir), str(plan)])
    return code, capsys.readouterr().out


def rules_named(printed):
    """The rule names in a check report, e.g. {'column rule'}."""
    names = set()
    for line in printed.splitlines():
        if line.startswith("Rule: "):
            names.add(line[len("Rule: "):].rsplit(" (", 1)[0])
    return names


@pytest.mark.parametrize("dataset, numbers", [
    (SMALL_DATASET, "7 papers, 7 room files, 48 seats, 14 duties"),
    (REALISTIC_DATASET, "56 papers, 454 room files, 8750 seats, 908 duties"),
])
def test_a_clean_plan_passes_and_nothing_is_written(dataset, numbers, tmp_path, capsys):
    plan = make_plan(tmp_path, capsys, dataset)
    before = sorted(plan.rglob("*"))
    code, printed = run_check(dataset, plan, capsys)
    assert code == 0, printed
    assert f"Plan check: no problems. {numbers} checked." in printed
    assert sorted(plan.rglob("*")) == before


# each breaks a fresh plan (and may change a copy of the input):
# function(plan folder, input folder)

def column_rule(plan, _):
    # BT2CSE0007 moves from column 3 to column 2, next to column 1
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0001,,CSE2001:BT2CSE0007",
                 "CSE2001:BT2CSE0001,CSE2001:BT2CSE0007,")


def wrong_paper_in_a_cell(plan, _):
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0002", "CSE2002:BT2CSE0002")


def student_not_in_input(plan, _):
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0002", "CSE2001:BT2CSE0099")


def student_seated_twice(plan, _):
    replace_once(plan / S02_2_NOV, "CSE2001:BT2ECOM0003,,\n",
                 "CSE2001:BT2ECOM0003,,CSE2001:BT2ECOM0001\n")


def student_with_no_seat(plan, _):
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0006", "")


def roll_order(plan, _):
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0001", "CSE2001:X")
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0002", "CSE2001:BT2CSE0001")
    replace_once(plan / S01_2_NOV, "CSE2001:X", "CSE2001:BT2CSE0002")


def one_paper_per_column(plan, _):
    # PHY2002's BT2ECOM0006 moves from column 2 into column 1 (MTH2001)
    replace_once(plan / S01_6_NOV, ",PHY2002:BT2ECOM0006,", ",,")
    replace_once(plan / S01_6_NOV, "\n,,\n", "\nPHY2002:BT2ECOM0006,,\n")


def gap(_, input_dir):
    # the plan was made with a gap of 2 days
    replace_once(input_dir / "settings.yaml", "min_gap_days: 2", "min_gap_days: 3")


def holiday(_, input_dir):
    replace_once(input_dir / "settings.yaml", "holidays: []", "holidays: [2026-11-04]")


def same_paper(plan, _):
    replace_once(plan / "schedule.csv", "CSE2001;CSE2003", "CSE2001")


def date_moved_in_the_date_sheet_only(plan, _):
    replace_once(plan / "schedule.csv", "2026-11-04,morning,CSE2002",
                 "2026-11-05,morning,CSE2002")


def room_short_of_a_teacher(plan, _):
    replace_once(plan / "duties.csv", "2026-11-02,morning,S01,T001\n", "")


def teacher_in_two_rooms(plan, _):
    replace_once(plan / "duties.csv", "2026-11-02,morning,S02,T002",
                 "2026-11-02,morning,S02,T001")


def teacher_with_own_students(plan, _):
    # T003 teaches BT2ECOM_I and T005 teaches BT2CSE_I: swap their rooms
    duties = plan / "duties.csv"
    replace_once(duties, "2026-11-02,morning,S01,T003", "2026-11-02,morning,S01,X")
    replace_once(duties, "2026-11-02,morning,S02,T005", "2026-11-02,morning,S02,T003")
    replace_once(duties, "2026-11-02,morning,S01,X", "2026-11-02,morning,S01,T005")


def teacher_without_own_paper_duty(plan, _):
    # T003 teaches CSE2001; the PhD scholar T009 takes their place
    replace_once(plan / "duties.csv", "2026-11-02,morning,S01,T003",
                 "2026-11-02,morning,S01,T009")


def duty_in_an_unused_room(plan, _):
    with open(plan / "duties.csv", "a", encoding="utf-8") as file:
        file.write("2026-11-02,morning,M01,T009\n")


def unknown_teacher(plan, _):
    replace_once(plan / "duties.csv", "2026-11-02,morning,S01,T001",
                 "2026-11-02,morning,S01,T999")


def room_csv_with_a_row_missing(plan, _):
    lines = (plan / S01_2_NOV).read_text(encoding="utf-8").splitlines(keepends=True)
    (plan / S01_2_NOV).write_text("".join(lines[:-1]), encoding="utf-8")


def bad_cell(plan, _):
    replace_once(plan / S01_2_NOV, "CSE2001:BT2CSE0002", "CSE2001-BT2CSE0002")


def extra_file(plan, _):
    (plan / "notes.txt").write_text("hello", encoding="utf-8")


def missing_duties_csv(plan, _):
    (plan / "duties.csv").unlink()


# (how it is broken, the rules named, texts the report must hold)
BROKEN_PLANS = [
    (column_rule, {"column rule"},
     ["S01.csv, columns 1 and 2: CSE2001 sits in both",
      "column 1: rows 1, 2, 3, 4, 5, 6 (BT2CSE0001,", "column 2: row 1 (BT2CSE0007)"]),
    # only that cell, not also "a CSE2001 student has no seat"
    (wrong_paper_in_a_cell, {"paper in its slot"},
     ["1 problem(s)", "S01.csv row 2, column 1: CSE2002 sits here on 2026-11-02"]),
    # both: the checker can't tell which missing student belonged in that seat
    (student_not_in_input, {"registration", "seated once"},
     ["BT2CSE0099 is not a student", "no seat for 1 registered student(s): BT2CSE0002",
      "can't tell which missing student belonged there"]),
    (student_seated_twice, {"seated once"}, ["BT2ECOM0001 has 2 seats"]),
    (student_with_no_seat, {"seated once"},
     ["no seat for 1 registered student(s): BT2CSE0006"]),
    (roll_order, {"roll order"}, ["BT2CSE0002"]),
    (one_paper_per_column, {"one paper per column"}, ["share one seat column"]),
    (gap, {"gap"}, ["CSE2001 (2026-11-02) and CSE2002 (2026-11-04) are 2 day(s) apart"]),
    (holiday, {"exam days"}, ["CSE2002 is on 2026-11-04, a holiday"]),
    (same_paper, {"same paper"}, ["CSE2001 lists CSE2001, but its course codes are"]),
    (date_moved_in_the_date_sheet_only, {"paper in its slot"}, ["1 problem(s)"]),
    (room_short_of_a_teacher, {"teachers per room"},
     ["S01 on 2026-11-02 morning has 1 teacher(s) (T003)"]),
    (teacher_in_two_rooms, {"one duty per slot"}, ["T001 has 2 duties on 2026-11-02 morning"]),
    (teacher_with_own_students, {"own students"},
     ["T003 is in S02 on 2026-11-02 morning, with their own students"]),
    (teacher_without_own_paper_duty, {"own paper duty"},
     ["T003 teaches CSE2001 (2026-11-02 morning)"]),
    (duty_in_an_unused_room, {"duty in a used room"}, ["no student sits there then"]),
    (unknown_teacher, {"known teacher"}, ["T999 is not in teachers.csv"]),
    # stage 1 problems stop the checker before the other rules
    (room_csv_with_a_row_missing, {"room shape"}, ["Fix these first"]),
    (bad_cell, {"room cell"}, ["should be PAPER:STUDENT or empty"]),
    (extra_file, {"output files"}, ["notes.txt: a plan folder holds only"]),
    (missing_duties_csv, {"output files"}, ["duties.csv is missing"]),
]


@pytest.mark.parametrize("break_it, rules, texts", BROKEN_PLANS,
                         ids=[case[0].__name__ for case in BROKEN_PLANS])
def test_a_broken_plan_names_the_rule(break_it, rules, texts, small_copy, tmp_path, capsys):
    plan = make_plan(tmp_path, capsys)
    break_it(plan, small_copy)
    code, printed = run_check(small_copy, plan, capsys)
    assert code == 3
    assert rules_named(printed) == rules
    for text in texts:
        assert text in printed


def test_a_folder_with_only_why_txt_gives_exit_2(tmp_path, capsys):
    dataset = IMPOSSIBLE_DATASETS / "too_few_teachers"
    plan = make_plan(tmp_path, capsys, dataset)
    code, printed = run_check(dataset, plan, capsys)
    assert code == 2
    assert "No plan in this folder" in printed
    assert "Rule: duties" in printed


def test_an_input_or_plan_that_cant_be_read_gives_exit_1(small_copy, tmp_path, capsys):
    plan = make_plan(tmp_path, capsys)
    code, printed = run_check(tmp_path / "nothing", plan, capsys)
    assert code == 1 and printed.startswith("Can't check: the input folder")

    code, printed = run_check(small_copy, tmp_path / "no_plan_here", capsys)
    assert code == 1 and "the plan folder" in printed

    (small_copy / "rooms.csv").unlink()
    code, printed = run_check(small_copy, plan, capsys)
    assert code == 1 and "rooms.csv is missing" in printed

    shutil.rmtree(small_copy)
    shutil.copytree(SMALL_DATASET, small_copy)
    (small_copy / "settings.yaml").write_text("start_date: 2026-11-40\n", encoding="utf-8")
    code, printed = run_check(small_copy, plan, capsys)
    assert code == 1 and "can't be read (day is out of range for month)" in printed
