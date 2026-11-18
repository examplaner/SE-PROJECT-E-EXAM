"""Test keyboard navigation without changing data or opening native dialogs."""

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import menu
from input_selection import MAIN_DATA


def data_path(item):
    if item.key == "students":
        return MAIN_DATA / "sections"
    suffix = ".yaml" if item.key in ("settings", "constraints") else ".csv"
    return MAIN_DATA / (item.key + suffix)


class MenuTests(unittest.TestCase):
    def run_menu(self, actions, picker=None, check=None):
        frames = []
        options = {}
        if check is not None:
            options["check_path"] = check
        result = menu.select_inputs(
            Mock(side_effect=[*actions, EOFError()]),
            lambda selected, current, message: frames.append(
                (dict(selected), current, message)),
            picker=picker if picker is not None else lambda item, previous: data_path(item),
            **options)
        return result, frames

    def test_success_advances_through_all_inputs_to_continue(self):
        result, frames = self.run_menu(["enter"] * (len(menu.INPUTS) + 1))
        self.assertEqual(result, {item.key: data_path(item) for item in menu.INPUTS})
        self.assertEqual([frame[1] for frame in frames], list(range(10)))

    def test_delete_only_clears_highlighted_choice_and_does_not_move(self):
        teacher = data_path(menu.INPUTS[0])
        original_bytes = teacher.read_bytes()
        _, frames = self.run_menu(["enter", "enter", "up", "up", "delete"])
        selected, current, message = frames[-1]
        self.assertNotIn("teachers", selected)
        self.assertEqual(selected["courses"], data_path(menu.INPUTS[1]))
        self.assertEqual(current, 0)
        self.assertIn("No file was deleted", message)
        self.assertEqual(teacher.read_bytes(), original_bytes)

    def test_cancel_replacement_keeps_highlight_and_all_choices(self):
        picker = Mock(side_effect=[data_path(menu.INPUTS[0]),
                                   data_path(menu.INPUTS[1]), None])
        _, frames = self.run_menu(["enter", "enter", "up", "up", "enter"], picker)
        selected, current, message = frames[-1]
        self.assertEqual(set(selected), {"teachers", "courses"})
        self.assertEqual(current, 0)
        self.assertIn("Cancelled", message)
        self.assertEqual(picker.call_args.args[1], data_path(menu.INPUTS[0]))

    def test_invalid_replacement_does_not_discard_old_selection(self):
        old = data_path(menu.INPUTS[0])
        _, frames = self.run_menu(["enter", "up", "enter"],
                                 Mock(side_effect=[old, MAIN_DATA / "settings.yaml"]))
        self.assertEqual(frames[-1][0]["teachers"], old)
        self.assertEqual(frames[-1][1], 0)
        self.assertIn(".csv", frames[-1][2])

    def test_replacement_advances_past_already_selected_input(self):
        replacement = MAIN_DATA / "rooms.csv"
        _, frames = self.run_menu(["enter", "enter", "up", "up", "enter"],
                                 Mock(side_effect=[data_path(menu.INPUTS[0]),
                                                   data_path(menu.INPUTS[1]), replacement]))
        self.assertEqual(frames[-1][0]["teachers"], replacement)
        self.assertEqual(frames[-1][1], 2)

    def test_continue_focuses_first_missing_input(self):
        result, frames = self.run_menu(["enter", "up", "up", "up", "enter"])
        self.assertIsNone(result)
        self.assertEqual(frames[-1][1], 1)
        self.assertIn("Select this input first", frames[-1][2])

    def test_continue_rechecks_paths_that_changed_since_selection(self):
        calls = 0

        def check(item, path):
            nonlocal calls
            calls += 1
            return "File no longer exists." if calls == 10 else None

        _, frames = self.run_menu(["enter"] * 10, check=check)
        self.assertEqual(frames[-1][1], 0)
        self.assertIn("no longer exists", frames[-1][2])
        self.assertEqual(len(frames[-1][0]), 9)

    def test_delete_continue_is_not_an_exit_or_bulk_clear(self):
        _, frames = self.run_menu(["enter"] * 9 + ["delete"])
        self.assertEqual(len(frames[-1][0]), 9)
        self.assertEqual(frames[-1][1], 9)

    def test_picker_error_and_back_keep_previous_choices(self):
        picker = Mock(side_effect=[data_path(menu.INPUTS[0]), RuntimeError("Cannot open picker")])
        _, frames = self.run_menu(["enter", "enter", "back"], picker)
        self.assertEqual(frames[-1][0], {"teachers": data_path(menu.INPUTS[0])})
        self.assertEqual(frames[-1][1], 1)
        self.assertTrue(any("Cannot open picker" in frame[2] for frame in frames))

    def test_exit_and_wrapped_navigation(self):
        picker = Mock()
        result, frames = self.run_menu(["up", "enter"], picker)
        self.assertIsNone(result)
        self.assertEqual(frames[-1][1], len(menu.INPUTS) + 1)
        picker.assert_not_called()

    def test_windows_extended_keys_are_decoded(self):
        for characters, action in [(["\xe0", "H"], "up"),
                                   (["\x00", "P"], "down"),
                                   (["\xe0", "S"], "delete"),
                                   (["\xe0", "K"], "ignore"),
                                   (["\r"], "enter"), (["\x1b"], "back")]:
            with self.subTest(characters=characters):
                self.assertEqual(menu.read_key(Mock(side_effect=characters)), action)

    def test_small_terminal_keeps_highlighted_exit_visible(self):
        stream = io.StringIO()
        with patch.object(menu.sys, "stdout", stream), \
                patch.object(menu.shutil, "get_terminal_size", return_value=(60, 12)):
            menu.draw_menu({}, 10, "Choose an input.")
        output = stream.getvalue()
        self.assertIn("\x1b[7m> Exit\x1b[0m", output)
        self.assertLess(len(output.splitlines()), 12)


if __name__ == "__main__":
    unittest.main()
