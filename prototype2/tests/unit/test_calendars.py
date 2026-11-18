"""The dates behind the two calendars (ExamCalendar). The windows themselves
need a person: see the steps to try them in REFACTOR_REPORT.md."""

import copy
from datetime import date

import pytest

import planner
from calendars import ExamCalendar
from conftest import REALISTIC_EXAMPLE


@pytest.fixture
def settings():
    # 2 to 20 Nov 2026, Mon to Fri, holiday 11 Nov
    return planner.read_settings(REALISTIC_EXAMPLE / "settings.yaml")


def test_the_settings_weekdays_and_holidays_start_marked(settings):
    exam_calendar = ExamCalendar.from_settings(settings)
    assert exam_calendar.excluded(date(2026, 11, 7))  # Saturday
    assert exam_calendar.excluded(date(2026, 11, 11))  # holiday
    assert not exam_calendar.excluded(date(2026, 11, 10))


def test_a_weekend_day_can_be_allowed_for_this_run_only(settings):
    original = copy.deepcopy(settings)
    exam_calendar = ExamCalendar.from_settings(settings)
    saturday = date(2026, 11, 7)
    exam_calendar.switch(saturday)
    run_settings = exam_calendar.effective_settings()
    assert "Sat" in run_settings["exam_weekdays"]
    assert saturday not in run_settings["holidays"]
    # neither the settings read from the file nor the calendar's copy change
    assert settings == original
    assert exam_calendar.settings == original


def test_a_longer_range_keeps_switched_days_and_marks_new_weekends(settings):
    exam_calendar = ExamCalendar.from_settings(settings)
    exam_calendar.switch(date(2026, 11, 10))
    exam_calendar.end = date(2026, 11, 30)
    assert exam_calendar.excluded(date(2026, 11, 10))
    assert exam_calendar.excluded(date(2026, 11, 28))  # Saturday
    assert not exam_calendar.excluded(date(2026, 11, 30))


def test_shrinking_then_widening_the_range_keeps_earlier_choices(settings):
    exam_calendar = ExamCalendar.from_settings(settings)
    day = date(2026, 11, 19)
    exam_calendar.switch(day)
    exam_calendar.end = date(2026, 11, 13)
    assert day not in exam_calendar.effective_settings()["holidays"]
    exam_calendar.end = date(2026, 11, 20)
    assert day in exam_calendar.effective_settings()["holidays"]


def test_a_one_day_range_on_a_leap_day(settings):
    exam_calendar = ExamCalendar.from_settings(settings)
    exam_calendar.start = exam_calendar.end = date(2028, 2, 29)
    exam_calendar.switch(date(2028, 2, 29))
    assert exam_calendar.effective_settings()["holidays"] == [date(2028, 2, 29)]


def test_a_day_outside_the_range_or_a_backwards_range_is_refused(settings):
    exam_calendar = ExamCalendar.from_settings(settings)
    with pytest.raises(ValueError):
        exam_calendar.switch(date(2026, 12, 1))
    exam_calendar.end = date(2026, 1, 1)
    with pytest.raises(ValueError):
        exam_calendar.effective_settings()
