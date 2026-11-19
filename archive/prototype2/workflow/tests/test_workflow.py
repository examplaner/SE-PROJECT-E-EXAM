"""Calendar, back/retry flow, and real-main generation checks."""

import copy
from datetime import date
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import calendars
import flow
import planner

MAIN = Path(__file__).resolve().parents[3] / "prototype1" / "data" / "main"


def main_inputs():
    keys = ["teachers", "courses", "sections", "registrations", "rooms", "teaching"]
    result = {key: MAIN / (key + ".csv") for key in keys}
    result.update(students=MAIN / "sections", settings=MAIN / "settings.yaml",
                  constraints=MAIN / "constraints.yaml")
    return result


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.settings = planner.read_settings(MAIN / "settings.yaml")
        self.state = calendars.ExamCalendar.from_settings(self.settings)

    def test_file_weekdays_and_holiday_are_preselected(self):
        self.assertTrue(self.state.excluded(date(2026, 11, 7)))
        self.assertTrue(self.state.excluded(date(2026, 11, 11)))
        self.assertFalse(self.state.excluded(date(2026, 11, 10)))

    def test_weekend_can_be_allowed_for_this_run_only(self):
        original = copy.deepcopy(self.settings)
        saturday = date(2026, 11, 7)
        self.state.toggle(saturday)
        effective = self.state.effective_settings()
        self.assertIn("Sat", effective["exam_weekdays"])
        self.assertNotIn(saturday, effective["holidays"])
        self.assertEqual(self.settings, original)
        self.assertEqual(self.state.settings, original)

    def test_extend_range_keeps_overrides_and_applies_existing_weekdays(self):
        day = date(2026, 11, 10)
        self.state.toggle(day)
        self.state.end = date(2026, 11, 30)
        self.assertTrue(self.state.excluded(day))
        self.assertTrue(self.state.excluded(date(2026, 11, 28)))
        self.assertFalse(self.state.excluded(date(2026, 11, 30)))

    def test_shrinking_then_extending_range_preserves_prior_choices(self):
        day = date(2026, 11, 19)
        self.state.toggle(day)
        self.state.end = date(2026, 11, 13)
        self.assertNotIn(day, self.state.effective_settings()["holidays"])
        self.state.end = date(2026, 11, 20)
        self.assertIn(day, self.state.effective_settings()["holidays"])

    def test_leap_year_and_single_day_range(self):
        self.state.start = self.state.end = date(2028, 2, 29)
        self.state.toggle(self.state.start)
        self.assertEqual(self.state.effective_settings()["holidays"], [date(2028, 2, 29)])

    def test_invalid_range_and_outside_click(self):
        with self.assertRaises(ValueError):
            self.state.toggle(date(2026, 12, 1))
        self.state.end = date(2026, 1, 1)
        with self.assertRaises(ValueError):
            self.state.effective_settings()


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.backend.InputProblem = planner.InputProblem
        self.backend.NoPlan = planner.NoPlan
        self.backend.TERMS = planner.TERMS
        self.backend.read_settings.return_value = planner.read_settings(MAIN / "settings.yaml")
        self.backend.recovery_for.side_effect = planner.recovery_for
        self.backend.save_failure.return_value = Path("why.txt")
        self.backend.generate_timetable.return_value = SimpleNamespace(folder=Path("saved"))
        self.backend.generate_seating.return_value = (Path("seating"),
            {"papers": 56, "room files": 454, "seats": 8750, "duties": 908})
        self.ui = Mock()
        self.visits = []
        self.input_calls = 0

        def inputs(selected):
            self.visits.append(dict(selected))
            self.input_calls += 1
            selected.update(main_inputs())
            return self.input_calls == 1

        self.ui.inputs.side_effect = inputs
        self.ui.dates.side_effect = lambda state, mode: ("continue", state)

    def test_no_timetable_goes_back_without_losing_inputs(self):
        self.ui.choose.return_value = 1
        flow.run_workflow(self.ui, self.backend)
        self.assertEqual(self.visits[1], main_inputs())
        self.backend.generate_timetable.assert_not_called()

    def test_no_seating_preserves_timetable_and_returns_to_selection(self):
        self.ui.choose.side_effect = [0, 1]
        flow.run_workflow(self.ui, self.backend)
        self.backend.generate_timetable.assert_called_once()
        self.backend.generate_seating.assert_not_called()
        self.assertEqual(self.visits[1], main_inputs())

    def test_gap_failure_returns_to_calendar_then_retry_uses_extended_range(self):
        self.backend.generate_timetable.side_effect = [
            planner.NoPlan("No plan possible.\nRule: gap\nWindow is too short."),
            SimpleNamespace(folder=Path("saved"))]
        range_visits = []

        def dates(state, mode):
            if mode == "range":
                range_visits.append(state.end)
                if len(range_visits) == 2:
                    state.end = date(2026, 11, 30)
            return "continue", state

        self.ui.dates.side_effect = dates
        self.ui.choose.side_effect = [0, 0, 0, 1]
        flow.run_workflow(self.ui, self.backend)
        self.assertEqual(self.input_calls, 1)
        self.assertEqual(len(range_visits), 2)
        self.assertEqual(self.backend.generate_timetable.call_args.args[1]["end_date"], date(2026, 11, 30))
        self.assertIn(str(planner.TERMS), self.ui.message.call_args.args[0])
        self.backend.generate_seating.assert_called_once()

    def test_other_failure_allows_input_recovery(self):
        self.backend.generate_timetable.side_effect = planner.NoPlan("No plan possible.\nRule: seats\nToo few seats.")
        self.ui.choose.side_effect = [0, 1]
        flow.run_workflow(self.ui, self.backend)
        self.assertEqual(self.visits[1], main_inputs())

    def test_calendar_back_preserves_inputs_and_calendar(self):
        self.ui.dates.side_effect = lambda state, mode: ("back", state)
        flow.run_workflow(self.ui, self.backend)
        self.assertEqual(self.visits[1], main_inputs())
        self.backend.generate_timetable.assert_not_called()


class GenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="exam-workflow-test-")
        cls.selected = main_inputs()
        cls.before = planner.fingerprints(cls.selected)
        cls.settings = calendars.ExamCalendar.from_settings(
            planner.read_settings(cls.selected["settings"])).effective_settings()
        cls.plan = planner.generate_timetable(cls.selected, cls.settings, cls.temp.name)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_main_timetable_is_written_without_seating_files(self):
        self.assertEqual(len(self.plan.placements), 56)
        self.assertTrue((self.plan.folder / "timetable/schedule.csv").is_file())
        self.assertTrue((self.plan.folder / "timetable/terms.md").is_file())
        self.assertFalse((self.plan.folder / "timetable/daywise_seating_plans").exists())

    def test_full_main_seating_passes_independent_checker(self):
        folder, counts = planner.generate_seating(self.plan)
        self.assertEqual(counts["room files"], 454)
        self.assertEqual(counts["duties"], 908)
        self.assertEqual(counts["seats"], 8750)
        self.assertTrue((folder / "daywise_seating_plans").is_dir())
        second, _ = planner.generate_seating(self.plan)
        self.assertNotEqual(folder, second)

    def test_failure_is_existing_engine_message_and_only_why_is_written(self):
        settings = dict(self.settings, end_date=date(2026, 11, 4))
        with self.assertRaises(planner.NoPlan) as caught:
            planner.generate_timetable(self.selected, settings, self.temp.name)
        self.assertIn("Rule: gap", str(caught.exception))
        why = planner.save_failure(caught.exception, self.temp.name)
        self.assertEqual([p.name for p in why.parent.iterdir()], ["why.txt"])
        self.assertEqual(why.read_text().strip(), str(caught.exception).strip())
        self.assertEqual(planner.recovery_for(caught.exception), "dates")

    def test_missing_course_file_is_reported_without_creating_output(self):
        selected = dict(self.selected, courses=MAIN / "not-present.csv")
        with self.assertRaises(planner.InputProblem):
            planner.load_selected(selected, self.settings)

    def test_all_original_inputs_remain_unchanged(self):
        self.assertEqual(planner.fingerprints(self.selected), self.before)


if __name__ == "__main__":
    unittest.main()
