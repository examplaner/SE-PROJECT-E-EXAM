"""Check navigation with controlled dialogs and the existing main dataset."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import input_selection as ui


def main_path(item):
    if item.key == "students":
        return ui.MAIN_DATA / "sections"
    suffix = ".yaml" if item.key in {"settings", "constraints"} else ".csv"
    return ui.MAIN_DATA / (item.key + suffix)


class InputSelectionTests(unittest.TestCase):
    def run_menu(self, choices, picker):
        messages = []
        result = ui.select_inputs(picker=picker, read=Mock(side_effect=choices),
                                  write=messages.append)
        return result, messages

    def test_select_all_existing_main_inputs(self):
        result, messages = self.run_menu(
            [str(n) for n in range(1, 10)] + ["done"],
            lambda item, previous: main_path(item))
        self.assertEqual(result, {item.key: main_path(item) for item in ui.INPUTS})
        self.assertTrue(any("selection complete" in line for line in messages))

    def test_cancel_replacement_keeps_previous_and_other_choices(self):
        visits = []

        def picker(item, previous):
            visits.append((item.key, previous))
            return None if previous else main_path(item)

        result, messages = self.run_menu(
            ["1", "2", "1"] + [str(n) for n in range(3, 10)] + ["done"], picker)
        self.assertEqual(visits[2], ("teachers", main_path(ui.INPUTS[0])))
        self.assertEqual(result["teachers"], main_path(ui.INPUTS[0]))
        self.assertEqual(result["courses"], main_path(ui.INPUTS[1]))
        self.assertIn("Back to inputs. All previous selections are kept.", messages)

    def test_cancel_first_picker_does_not_exit(self):
        picker = Mock(return_value=None)
        result, messages = self.run_menu(["1", "done", "q"], picker)
        self.assertIsNone(result)
        self.assertTrue(any(line.startswith("Still needed:") for line in messages))

    def test_invalid_replacement_keeps_original(self):
        def picker(item, previous):
            return ui.MAIN_DATA / "settings.yaml" if previous else main_path(item)

        result, messages = self.run_menu(
            ["1", "1"] + [str(n) for n in range(2, 10)] + ["done"], picker)
        self.assertEqual(result["teachers"], main_path(ui.INPUTS[0]))
        self.assertTrue(any("Select a file ending in .csv" in line for line in messages))

    def test_picker_failure_and_interrupt_preserve_choices(self):
        calls = 0

        def picker(item, previous):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("Picker unavailable")
            if calls == 3:
                raise KeyboardInterrupt
            return main_path(item)

        result, messages = self.run_menu(
            ["1", "2", "2"] + [str(n) for n in range(2, 10)] + ["done"], picker)
        self.assertEqual(result["teachers"], main_path(ui.INPUTS[0]))
        self.assertTrue(any("Picker unavailable" in line for line in messages))

    def test_invalid_menu_entries_do_not_open_picker(self):
        picker = Mock()
        self.run_menu(["", "0", "10", "-1", "abc", "1.5", "q"], picker)
        picker.assert_not_called()

    def test_closed_terminal_exits_cleanly(self):
        result, messages = self.run_menu([EOFError()], Mock())
        self.assertIsNone(result)
        self.assertTrue(any("Terminal input closed" in line for line in messages))

    def test_path_checks_reject_wrong_kind_and_missing_path(self):
        teacher, students = ui.INPUTS[0], ui.INPUTS[3]
        self.assertIsNotNone(ui.path_problem(teacher, ui.MAIN_DATA))
        self.assertIsNotNone(ui.path_problem(students, main_path(teacher)))
        self.assertIsNotNone(ui.path_problem(teacher, ui.MAIN_DATA / "missing.csv"))

    def test_empty_folder_and_permission_error(self):
        path = Mock()
        path.is_dir.return_value = True
        path.iterdir.return_value = iter(())
        self.assertIn("no CSV files", ui.path_problem(ui.INPUTS[3], path))
        path.iterdir.side_effect = PermissionError("Access denied")
        self.assertIn("Cannot read", ui.path_problem(ui.INPUTS[3], path))

    def test_picker_uses_file_or_folder_dialog_and_destroys_window(self):
        for item in (ui.INPUTS[0], ui.INPUTS[3]):
            with self.subTest(item=item.key), patch("tkinter.Tk") as window, \
                    patch("tkinter.filedialog.askopenfilename", return_value="") as file_dialog, \
                    patch("tkinter.filedialog.askdirectory", return_value="") as folder_dialog:
                self.assertIsNone(ui.choose_path(item))
                (file_dialog if item.suffixes else folder_dialog).assert_called_once()
                (folder_dialog if item.suffixes else file_dialog).assert_not_called()
                window.return_value.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
