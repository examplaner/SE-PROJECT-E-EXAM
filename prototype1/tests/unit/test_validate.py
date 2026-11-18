"""Input checks (data_design_spec.md section 3): break a copy of the small
dataset on purpose, and main.py stops with exit code 1 and names the problem."""

import pytest

from conftest import REALISTIC_DATASET, SMALL_DATASET, replace_once, run_main


def add_line(path, line):
    with open(path, "a", encoding="utf-8") as file:
        file.write(line + "\n")


@pytest.mark.parametrize("dataset", [SMALL_DATASET, REALISTIC_DATASET])
def test_both_datasets_are_valid(dataset, tmp_path, capsys):
    code, printed, _ = run_main(dataset, tmp_path / "out", capsys)
    assert code == 0, printed
    assert printed.startswith("Input OK")


def test_missing_input_folder(tmp_path, capsys):
    code, printed, folder = run_main(tmp_path / "nope", tmp_path / "out", capsys)
    assert code == 1
    assert "folder not found" in printed
    assert folder is None


# (file, line added at its end, text the report must hold)
BAD_LINES = [
    ("rooms.csv", "S99,S,6", "has 3 value(s), expected 4"),
    ("registrations.csv", "BT2CSE0001,CSE9999",
     "registrations.csv row 50: course code CSE9999 is not in courses.csv"),
    ("rooms.csv", "S01,M,7,6", "room_id S01 is already used in row 2"),
    ("sections/BT2ECOM_I.csv", "BT2CSE0001",
     "student BT2CSE0001 is already in sections/BT2CSE_I.csv row 2"),
    ("sections/BT2CSE_I.csv", "BT2CSE0099", "student BT2CSE0099 has no registrations"),
    ("registrations.csv", "BT2CSE0001,ECE2001",
     "BT2CSE0001 is in cohort BT2CSE, but ECE2001 is offered to BT2ECOM"),
    ("courses.csv", "CSE2099,Empty Course,BT2CSE,ELECTIVE",
     "nobody is registered for CSE2099, so it has no exam"),
    ("registrations.csv", "BT2CSE0001,CSE2001", "BT2CSE0001 CSE2001 is already in row 2"),
    ("rooms.csv", "L01,L,abc,6", "type of L01 is L"),
    ("rooms.csv", "L01,L,abc,6", "rows of L01 is abc"),
    ("teachers.csv", "T999,DEAN", "rank of T999 is DEAN"),
    ("teaching.csv", "T001,ECE2001,BT2CSE_I",
     "ECE2001 is offered to BT2ECOM, but BT2CSE_I is in BT2CSE"),
]


@pytest.mark.parametrize("file_name, line, expected", BAD_LINES)
def test_a_bad_line_is_named(small_copy, tmp_path, capsys, file_name, line, expected):
    add_line(small_copy / file_name, line)
    code, printed, folder = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert expected in printed
    assert folder is None


def test_missing_file(small_copy, tmp_path, capsys):
    (small_copy / "rooms.csv").unlink()
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "rooms.csv: file is missing" in printed


def test_bad_header_gives_one_error_not_a_flood(small_copy, tmp_path, capsys):
    replace_once(small_copy / "sections.csv", "section_id", "sectoin_id")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "Input is invalid: 1 problem(s)" in printed
    assert "sections.csv row 1: header should be" in printed
    assert "Fix these first" in printed


def test_broken_yaml(small_copy, tmp_path, capsys):
    (small_copy / "settings.yaml").write_text("start_date: [2026-11-02\n", encoding="utf-8")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "settings.yaml: cannot be read as YAML" in printed


def test_problems_are_grouped_by_rule_with_a_count(small_copy, tmp_path, capsys):
    add_line(small_copy / "registrations.csv", "BT2CSE0001,CSE9998")
    add_line(small_copy / "registrations.csv", "BT2CSE0002,CSE9999")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "[course code exists] 2 problem(s)" in printed
    # every problem is still listed
    assert "CSE9998" in printed and "CSE9999" in printed


def test_teaching_a_section_with_no_students_for_it(small_copy, tmp_path, capsys):
    # PHY2002 is a BT2ECOM elective; a second BT2ECOM section has one student
    # who does not take it, and someone is said to teach it there
    add_line(small_copy / "sections.csv", "BT2ECOM_II,BT2ECOM,BTECH,2")
    (small_copy / "sections" / "BT2ECOM_II.csv").write_text("student_id\nBT2ECOM0099\n",
                                                           encoding="utf-8")
    add_line(small_copy / "registrations.csv", "BT2ECOM0099,ECE2001")
    add_line(small_copy / "teaching.csv", "T001,PHY2002,BT2ECOM_II")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "no student of BT2ECOM_II is registered for PHY2002" in printed


def test_bad_settings(small_copy, tmp_path, capsys):
    settings = small_copy / "settings.yaml"
    replace_once(settings, "start_date: 2026-11-02", "start_date: 2026-11-30")
    replace_once(settings, "[morning, evening]", "[morning, afternoon, evening]")
    replace_once(settings, "min_gap_days: 2", "min_gap_days: 0")
    replace_once(settings, "holidays: []", "holidays: [Nov 11]")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "start_date 2026-11-30 is after end_date 2026-11-06" in printed
    assert "sessions should be two different names" in printed
    assert "min_gap_days should be a whole number of at least 1" in printed
    assert "holiday 'Nov 11' is not a date like 2026-11-11" in printed


def test_a_date_that_does_not_exist_is_reported_not_a_crash(small_copy, tmp_path, capsys):
    # PyYAML reads 2026-11-40 as a date and fails on it
    replace_once(small_copy / "settings.yaml", "holidays: []", "holidays: [2026-11-40]")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "settings.yaml: cannot be read as YAML (day is out of range for month)" in printed


def test_true_is_not_a_number_of_days(small_copy, tmp_path, capsys):
    # in Python True counts as 1, so it needs its own check
    replace_once(small_copy / "settings.yaml", "min_gap_days: 2", "min_gap_days: true")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "min_gap_days should be a whole number of at least 1, found True" in printed


def test_bad_constraints(small_copy, tmp_path, capsys):
    (small_copy / "constraints.yaml").write_text(
        "same_paper:\n- [CSE2001, CSE2003]\n- [CSE2003, CSE9999]\n- [PHY2001]\n",
        encoding="utf-8")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 1
    assert "same_paper group 2: CSE2003 is also in same_paper group 1" in printed
    assert "same_paper group 2: course code CSE9999 is not in courses.csv" in printed
    assert "same_paper group 3 ['PHY2001'] has 1 code(s)" in printed


def test_empty_lists_and_an_excel_byte_order_mark_are_fine(small_copy, tmp_path, capsys):
    replace_once(small_copy / "settings.yaml", "holidays: []", "holidays:")
    (small_copy / "constraints.yaml").write_text("", encoding="utf-8")
    rooms = small_copy / "rooms.csv"
    rooms.write_text("﻿" + rooms.read_text(encoding="utf-8") + "\n\n", encoding="utf-8")
    code, printed, _ = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 0, printed
