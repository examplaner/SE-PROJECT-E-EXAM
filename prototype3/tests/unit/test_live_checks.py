"""The app checks each file when it is chosen, and the rules across files
before the calendars open (that step of the flow is in test_flow.py)."""

import shutil

import pytest

import inputs
import planner
import terminal
from conftest import PROTOTYPE, SMALL_DATASET, inputs_of

BROKEN_REGISTRATIONS = PROTOTYPE / "data" / "invalid" / "registrations_unknown_course.csv"


def test_every_file_of_a_valid_dataset_passes_on_its_own():
    for key, path in inputs_of(SMALL_DATASET).items():
        assert terminal.check_input(inputs.input_named(key), path) is None, key


def test_a_file_with_the_wrong_header_is_refused_naming_the_picked_file():
    problem = terminal.check_input(inputs.input_named("teachers"), SMALL_DATASET / "rooms.csv")
    assert problem.startswith("Teachers: this file can't be used.")
    assert "rooms.csv row 1: header should be teacher_id,rank" in problem


def test_the_rules_of_one_file_run_when_it_is_chosen(small_copy):
    rooms = small_copy / "rooms.csv"
    rooms.write_text(rooms.read_text(encoding="utf-8") + "S01,S,6,3\n", encoding="utf-8")
    assert "room_id S01 is already used" in planner.file_problem("rooms", rooms)

    teachers = small_copy / "teachers.csv"
    teachers.write_text(teachers.read_text(encoding="utf-8") + "T999,DEAN\n", encoding="utf-8")
    assert "rank of T999 is DEAN" in planner.file_problem("teachers", teachers)

    settings = small_copy / "settings.yaml"
    text = settings.read_text(encoding="utf-8").replace("min_gap_days: 2", "min_gap_days: 0")
    settings.write_text(text, encoding="utf-8")
    assert "min_gap_days should be a whole number" in planner.file_problem("settings", settings)


def test_a_refused_file_keeps_the_old_choice(small_copy):
    wrong = small_copy / "wrong.csv"
    shutil.copy(small_copy / "rooms.csv", wrong)
    selected = {"teachers": (small_copy / "teachers.csv").resolve()}
    messages = []
    # choose Teachers, pick the wrong file, then exit
    answers = [0, "exit"]

    def ask(message, choices, default):
        return answers.pop(0)

    def pick(item, previous):
        return wrong

    assert inputs.pick_inputs(selected, ask, pick, terminal.check_input, messages.append) is False
    assert selected == {"teachers": (small_copy / "teachers.csv").resolve()}
    assert any("wrong.csv row 1: header should be teacher_id,rank" in text for text in messages)


def test_the_rules_across_files_name_the_picked_file():
    selected = inputs_of(SMALL_DATASET)
    selected["registrations"] = BROKEN_REGISTRATIONS
    # on its own the file is fine: only courses.csv knows CSE9999 is missing
    assert terminal.check_input(inputs.input_named("registrations"), BROKEN_REGISTRATIONS) is None
    settings = planner.read_settings(selected["settings"])
    with pytest.raises(planner.InputProblem) as error:
        planner.load_selected(selected, settings)
    assert ("registrations_unknown_course.csv row 50: course code CSE9999 is not in courses.csv"
            in str(error.value))


def test_the_broken_registrations_file_differs_from_tiny_by_one_row():
    broken = BROKEN_REGISTRATIONS.read_text(encoding="utf-8").splitlines()
    good = (SMALL_DATASET / "registrations.csv").read_text(encoding="utf-8").splitlines()
    assert broken == good + ["BT2CSE0001,CSE9999"]
    assert len(broken) == 50
