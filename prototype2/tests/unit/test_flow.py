"""The steps of the app and their back and retry loops, with a fake terminal
and a fake planner, so no window or menu opens."""

from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import flow
import planner
from conftest import REALISTIC_EXAMPLE, inputs_of

CHOSEN = inputs_of(REALISTIC_EXAMPLE)


class Run:
    """A fake terminal and planner. The person picks every input on the
    first visit to the inputs menu and exits on the next."""

    def __init__(self):
        self.visits = []
        self.ui = Mock()
        self.ui.pick_inputs.side_effect = self.pick_inputs
        self.ui.pick_dates.side_effect = lambda exam_calendar, mode: ("continue", exam_calendar)
        self.backend = Mock()
        self.backend.InputProblem = planner.InputProblem
        self.backend.NoPlan = planner.NoPlan
        self.backend.TERMS = planner.TERMS
        self.backend.read_settings.return_value = planner.read_settings(CHOSEN["settings"])
        self.backend.recovery_for.side_effect = planner.recovery_for
        self.backend.save_failure.return_value = Path("why.txt")
        self.backend.generate_timetable.return_value = SimpleNamespace(folder=Path("run"))
        self.backend.generate_seating.return_value = (
            Path("seating"), {"papers": 56, "room files": 454, "seats": 8750, "duties": 908})

    def pick_inputs(self, selected):
        # what was already chosen when the menu opened
        self.visits.append(dict(selected))
        selected.update(CHOSEN)
        return len(self.visits) == 1

    def go(self):
        flow.run_workflow(self.ui, self.backend)


@pytest.fixture
def run():
    return Run()


def test_no_to_the_timetable_goes_back_to_the_inputs_keeping_them(run):
    run.ui.confirm.return_value = False
    run.go()
    assert run.visits[1] == CHOSEN
    run.backend.generate_timetable.assert_not_called()


def test_no_to_the_seating_keeps_the_timetable_and_the_inputs(run):
    run.ui.confirm.side_effect = [True, False]
    run.go()
    run.backend.generate_timetable.assert_called_once()
    run.backend.generate_seating.assert_not_called()
    assert run.visits[1] == CHOSEN


def test_yes_twice_writes_the_seating_plan(run):
    run.ui.confirm.return_value = True
    run.ui.choose.return_value = 1  # Exit
    run.go()
    run.backend.generate_seating.assert_called_once()
    assert "Plan check passed: 56 papers, 454 room files" in run.ui.show.call_args.args[0]


def test_a_gap_failure_goes_back_to_the_calendar_and_retries_with_new_dates(run):
    run.backend.generate_timetable.side_effect = [
        planner.NoPlan("No plan possible.\nRule: gap\nThe window is too short."),
        SimpleNamespace(folder=Path("run"))]
    range_visits = []

    def pick_dates(exam_calendar, mode):
        if mode == "range":
            range_visits.append(exam_calendar.end)
            # on the second visit the person makes the window longer
            if len(range_visits) == 2:
                exam_calendar.end = date(2026, 11, 30)
        return "continue", exam_calendar

    run.ui.pick_dates.side_effect = pick_dates
    run.ui.confirm.return_value = True
    run.ui.choose.return_value = 1  # Exit
    run.go()
    assert len(run.visits) == 1
    assert len(range_visits) == 2
    assert run.backend.generate_timetable.call_args.args[1]["end_date"] == date(2026, 11, 30)
    assert str(planner.TERMS) in run.ui.pause.call_args.args[0]
    run.backend.generate_seating.assert_called_once()


def test_another_failure_lets_the_person_change_the_inputs(run):
    run.backend.generate_timetable.side_effect = planner.NoPlan(
        "No plan possible.\nRule: seats\nToo few seats.")
    run.ui.confirm.return_value = True
    run.ui.choose.return_value = 1  # Input files
    run.go()
    assert run.visits[1] == CHOSEN


def test_back_in_the_calendar_keeps_the_inputs(run):
    run.ui.pick_dates.side_effect = lambda exam_calendar, mode: ("back", exam_calendar)
    run.go()
    assert run.visits[1] == CHOSEN
    run.backend.generate_timetable.assert_not_called()


def test_a_bad_settings_file_stays_in_the_inputs_menu(run):
    run.backend.read_settings.side_effect = planner.InputProblem("settings.yaml: bad")
    run.go()
    assert len(run.visits) == 2
    assert "settings.yaml: bad" in run.ui.pause.call_args.args[0]
    run.ui.pick_dates.assert_not_called()
