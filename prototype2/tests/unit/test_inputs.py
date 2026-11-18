"""The inputs menu and the path checks, with scripted answers instead of a
person, so no menu or picker opens."""

from pathlib import Path
from unittest.mock import Mock, patch

import inputs
from conftest import REALISTIC_EXAMPLE, inputs_of

CHOSEN = inputs_of(REALISTIC_EXAMPLE)


class Menu:
    """Runs inputs.pick_inputs() with scripted menu answers and picker
    results, and records what the menu showed."""

    def __init__(self, answers, picked=None, check=inputs.path_problem):
        self.answers = list(answers)
        # what the picker returns, one per opening; by default the input's file
        self.picked = picked
        self.check = check
        # the value highlighted each time the main menu opened
        self.highlights = []
        self.messages = []
        self.pick_calls = []
        self.selected = {}

    def ask(self, message, choices, default):
        if message == "Exam planner - inputs":
            self.highlights.append(default)
        return self.answers.pop(0)

    def pick(self, item, previous):
        self.pick_calls.append((item.key, previous))
        if self.picked is None:
            return CHOSEN[item.key]
        result = self.picked.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def run(self):
        return inputs.pick_inputs(self.selected, self.ask, self.pick, self.check,
                                  self.messages.append)


def test_each_choice_moves_on_to_the_next_missing_input():
    menu = Menu(list(range(9)) + ["continue"])
    assert menu.run() is True
    assert menu.selected == {key: path.resolve() for key, path in CHOSEN.items()}
    assert menu.highlights == list(range(9)) + ["continue"]


def test_cancel_keeps_the_old_choice_and_every_other_one():
    # teachers and courses are chosen, then teachers again: Cancel
    teachers = CHOSEN["teachers"].resolve()
    menu = Menu([0, 1, 0, "exit"], picked=[teachers, CHOSEN["courses"], None])
    assert menu.run() is False
    assert menu.selected["teachers"] == teachers
    assert set(menu.selected) == {"teachers", "courses"}
    # the picker opened at the old choice, and the highlight stayed
    assert menu.pick_calls[2] == ("teachers", teachers)
    assert menu.highlights[-1] == 0
    assert "Cancelled. Previous choices kept." in menu.messages


def test_a_wrong_file_does_not_replace_the_old_choice():
    menu = Menu([0, 0, "exit"], picked=[CHOSEN["teachers"], CHOSEN["settings"]])
    menu.run()
    assert menu.selected["teachers"] == CHOSEN["teachers"].resolve()
    assert any("Choose a file ending in .csv" in message for message in menu.messages)


def test_a_picker_error_or_ctrl_c_keeps_every_choice():
    menu = Menu([0, 1, None, "exit"], picked=[CHOSEN["teachers"], RuntimeError("No picker")])
    menu.run()
    assert set(menu.selected) == {"teachers"}
    assert any("No picker" in message for message in menu.messages)
    assert any("All choices kept" in message for message in menu.messages)


def test_clearing_a_choice_leaves_its_file_and_the_other_choices():
    teachers = CHOSEN["teachers"]
    before = teachers.read_bytes()
    menu = Menu([0, 1, "clear", 0, "exit"])
    menu.run()
    assert set(menu.selected) == {"courses"}
    assert teachers.read_bytes() == before
    assert "Teachers cleared. No file was deleted." in menu.messages
    # the cleared input is highlighted, ready for its new file
    assert menu.highlights[-1] == 0


def test_continue_highlights_the_first_missing_input():
    menu = Menu([0, "continue", "exit"])
    assert menu.run() is False
    assert menu.highlights[-1] == 1
    assert "Courses: Choose this input first." in menu.messages


def test_continue_checks_the_paths_again():
    # every input is chosen, but then the teachers file goes missing
    checks = []

    def check(item, path):
        checks.append(item.key)
        # the first round of checks is the choosing; the next is Continue
        if len(checks) > len(inputs.INPUTS) and item.key == "teachers":
            return "The file no longer exists."
        return None

    menu = Menu(list(range(9)) + ["continue", "exit"], check=check)
    assert menu.run() is False
    assert menu.highlights[-1] == 0
    assert "Teachers: The file no longer exists." in menu.messages


def test_path_problem_names_what_is_wrong(tmp_path):
    teachers, students = inputs.INPUTS[0], inputs.INPUTS[3]
    assert "ending in .csv" in inputs.path_problem(teachers, CHOSEN["settings"])
    assert "does not exist" in inputs.path_problem(teachers, REALISTIC_EXAMPLE / "missing.csv")
    assert "does not exist" in inputs.path_problem(teachers, REALISTIC_EXAMPLE)
    assert "Choose a folder" in inputs.path_problem(students, CHOSEN["teachers"])
    assert "no CSV files" in inputs.path_problem(students, tmp_path)
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    assert "is empty" in inputs.path_problem(teachers, empty)
    assert inputs.path_problem(teachers, CHOSEN["teachers"]) is None
    assert inputs.path_problem(students, CHOSEN["students"]) is None


def test_a_folder_that_cant_be_read_is_a_problem_not_a_crash():
    folder = Mock(spec=Path)
    folder.is_dir.return_value = True
    folder.iterdir.side_effect = PermissionError("Access denied")
    assert "Can't read the chosen path" in inputs.path_problem(inputs.INPUTS[3], folder)


def test_a_file_opens_a_file_picker_and_a_folder_a_folder_picker():
    for item in (inputs.INPUTS[0], inputs.INPUTS[3]):
        with patch("tkinter.Tk") as window, \
                patch("tkinter.filedialog.askopenfilename", return_value="") as file_picker, \
                patch("tkinter.filedialog.askdirectory", return_value="") as folder_picker:
            # an empty answer is Cancel
            assert inputs.choose_path(item) is None
            if item.suffixes:
                file_picker.assert_called_once()
                folder_picker.assert_not_called()
            else:
                folder_picker.assert_called_once()
                file_picker.assert_not_called()
            window.return_value.destroy.assert_called_once()
