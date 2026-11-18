"""Exercise file selection through the workflow menu with real temporary CSVs."""

from contextlib import nullcontext
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

WORKFLOW = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKFLOW))
import interface
import planner


class LiveValidationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name) / "tiny"
        shutil.copytree(WORKFLOW.parents[1] / "prototype1/data/tiny", self.folder)
        self.inputs = {}
        for item in interface.INPUTS:
            if item.key == "students":
                self.inputs[item.key] = self.folder / "sections"
            else:
                self.inputs[item.key] = self.folder / (item.key + item.suffixes[0])

    def menu(self, selected, actions, paths):
        """Navigate to each named row and press its key, as in a real terminal."""
        keys = [item.key for item in interface.INPUTS] + ["continue", "exit"]
        actions = list(actions)
        messages = []
        errors = []
        current = None

        def draw(title, entries, index, detail):
            nonlocal current
            current = keys[index]
            messages.append(detail)

        def press():
            target, action = actions[0]
            if current != target:
                return "down"
            actions.pop(0)
            return action

        with (patch.object(interface.keyboard, "terminal_screen", nullcontext),
              patch.object(interface, "draw", draw),
              patch.object(interface.keyboard, "read_key", press),
              patch.object(interface, "choose_path", side_effect=paths),
              patch.object(interface, "show_validation_error", side_effect=errors.append)):
            continued = interface.TerminalUI().inputs(selected)
        self.assertFalse(actions)
        return continued, "\n".join(messages), [str(error) for error in errors]

    def test_bad_header_keeps_previous_selection(self):
        bad = self.folder / "wrong.csv"
        bad.write_text("sectoin_id,cohort_id,program,year\n")
        selected = {"sections": self.inputs["sections"]}
        _, _, errors = self.menu(selected, [("sections", "enter"), ("exit", "enter")], [bad])
        self.assertEqual(selected, {"sections": self.inputs["sections"]})
        self.assertIn("Stage 1", errors[0])
        self.assertIn("wrong.csv row 1: header should be section_id", errors[0])

    def test_duplicate_room_rejected_with_just_rooms(self):
        rooms = self.inputs["rooms"]
        with rooms.open("a") as stream:
            stream.write("S01,S,6,3\n")
        selected = {}
        _, _, errors = self.menu(selected, [("rooms", "enter"), ("exit", "enter")], [rooms])
        self.assertFalse(selected)
        self.assertIn("Stage 2", errors[0])
        self.assertIn("room_id S01 is already used", errors[0])

    def test_unknown_course_in_either_order_and_replacement(self):
        registrations = self.inputs["registrations"]
        bad = self.folder / "class-registrations.csv"
        bad.write_bytes(registrations.read_bytes() + b"BT2CSE0001,CSE9999\n")
        for first, second in [("registrations", "courses"), ("courses", "registrations")]:
            with self.subTest(first=first):
                selected = {}
                paths = {"courses": self.inputs["courses"], "registrations": bad}
                actions = [(first, "enter"), (second, "enter"), ("registrations", "enter"),
                           ("exit", "enter")]
                _, messages, errors = self.menu(selected, actions, [paths[first], paths[second], registrations])
                self.assertEqual(len(errors), 1)
                self.assertIn("Stage 2", errors[0])
                self.assertIn("class-registrations.csv row 50: course code CSE9999", errors[0])
                if first == "registrations":
                    self.assertIn("Course-code check pending", messages)
                self.assertEqual(selected, {"courses": paths["courses"], "registrations": registrations})
                planner.validate_selection(selected)

    def test_continue_rereads_files_before_calendar(self):
        selected = dict(self.inputs)
        with self.inputs["teachers"].open("a") as stream:
            stream.write("T999,DEAN\n")
        advanced, _, errors = self.menu(selected, [("continue", "enter"), ("exit", "enter")], [])
        self.assertFalse(advanced)
        self.assertIn("rank of T999 is DEAN", errors[0])
        self.assertEqual(selected, self.inputs)

    def test_every_prefix_of_valid_selection_can_continue_when_complete(self):
        selected = {}
        actions = [(key, "enter") for key in reversed(self.inputs)]
        paths = [self.inputs[key] for key, _ in actions]
        advanced, messages, errors = self.menu(selected, actions + [("continue", "enter")], paths)
        self.assertTrue(advanced)
        self.assertEqual(errors, [])
        self.assertEqual(selected, self.inputs)
        self.assertIn("Stages 1 and 2 passed for all inputs", messages)

    def test_empty_course_catalog_counts_as_selected(self):
        courses = self.inputs["courses"]
        courses.write_text("course_code,title,cohort_id,kind\n")
        with self.assertRaisesRegex(planner.InputProblem, "not in courses.csv"):
            planner.validate_selection({"registrations": self.inputs["registrations"], "courses": courses})

    def test_roster_and_shared_paper_checks_run_when_dependencies_arrive(self):
        (self.inputs["students"] / "EXTRA.csv").write_text("student_id\nEXTRA001\n")
        with self.assertRaisesRegex(planner.InputProblem, "section EXTRA is not in sections.csv"):
            planner.validate_selection({k: self.inputs[k] for k in ["students", "sections"]})
        self.inputs["constraints"].write_text("same_paper: [[CSE2001, UNKNOWN]]\n")
        planner.validate_selection({"constraints": self.inputs["constraints"]})
        with self.assertRaisesRegex(planner.InputProblem, "UNKNOWN is not in courses.csv"):
            planner.validate_selection({k: self.inputs[k] for k in ["constraints", "courses"]})

    def test_generation_rechecks_source_settings_after_calendar(self):
        path = self.inputs["settings"]
        effective = planner.read_settings(path)
        path.write_text("start_date: [\n")
        with self.assertRaisesRegex(planner.InputProblem, "Stage 1"):
            planner.load_selected(self.inputs, effective)
        path.write_text("sessions: [only]\n")
        with self.assertRaisesRegex(planner.InputProblem, "Stage 2"):
            planner.load_selected(self.inputs, effective)
