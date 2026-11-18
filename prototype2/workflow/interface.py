"""Terminal choices and native pickers, with persistent input selections."""

from dataclasses import replace
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "keyboard_cli"))
import menu as keyboard
from input_selection import INPUTS as OLD_INPUTS, choose_path, path_problem
from calendars import choose_dates

INPUTS = tuple(replace(item, label="Who teaches what") if item.key == "teaching" else item
               for item in OLD_INPUTS)


def draw(title, entries, current, detail=""):
    columns, rows = shutil.get_terminal_size((100, 30))
    width = max(1, columns - 1)
    heading = [title, "Up/Down Move | Enter Select | Delete Clear input | Esc Back", ""]
    visible = max(1, rows - 9)
    start = max(0, min(current - visible + 1, len(entries) - visible))
    lines = [line[:width] + "\x1b[K" for line in heading]
    for index in range(start, min(len(entries), start + visible)):
        text = (("> " if index == current else "  ") + entries[index])[:width]
        lines.append(("\x1b[7m" + text + "\x1b[0m" if index == current else text) + "\x1b[K")
    lines.append("\x1b[K")
    lines.extend(line[:width] + "\x1b[K" for line in str(detail).splitlines()[:4])
    sys.stdout.write("\x1b[H" + "\n".join(lines) + "\x1b[J")
    sys.stdout.flush()


class TerminalUI:
    def report(self, text):
        print(text, flush=True)

    def message(self, text):
        self.report(text)
        try:
            input("Press Enter to go back and adjust your choices...")
        except KeyboardInterrupt:
            pass

    def choose(self, title, options, detail=""):
        current = 0
        with keyboard.terminal_screen():
            while True:
                draw(title, options, current, detail)
                try:
                    action = keyboard.read_key()
                except KeyboardInterrupt:
                    return len(options) - 1
                if action in ("up", "down"):
                    current = (current + (1 if action == "down" else -1)) % len(options)
                elif action == "enter":
                    return current
                elif action == "back":
                    return len(options) - 1

    def inputs(self, selected):
        """Edit the same dictionary on each visit so Back cannot erase progress."""
        current = next((i for i, item in enumerate(INPUTS) if item.key not in selected), len(INPUTS))
        message = "Choose an input. Your previous choices stay selected when you return."
        with keyboard.terminal_screen():
            while True:
                entries = [f"{'[x]' if item.key in selected else '[ ]'} {item.label}: "
                           f"{selected[item.key].name if item.key in selected else 'Not selected'}"
                           for item in INPUTS] + ["Continue to exam dates", "Exit"]
                detail = message
                if current < len(INPUTS) and INPUTS[current].key in selected:
                    detail += "\n" + str(selected[INPUTS[current].key])
                draw("Exam planner - inputs", entries, current, detail)
                try:
                    action = keyboard.read_key()
                    if action in ("up", "down"):
                        current = (current + (1 if action == "down" else -1)) % len(entries)
                    elif action == "delete" and current < len(INPUTS):
                        item = INPUTS[current]
                        selected.pop(item.key, None)
                        message = f"{item.label} cleared. No file was deleted."
                    elif action == "back":
                        message = "All choices kept. Select Exit if you want to leave."
                    elif action == "enter":
                        if current == len(INPUTS) + 1:
                            return False
                        if current == len(INPUTS):
                            for index, item in enumerate(INPUTS):
                                problem = (path_problem(item, selected[item.key])
                                           if item.key in selected else "Select this input first.")
                                if problem:
                                    current, message = index, problem
                                    break
                            else:
                                return True
                            continue
                        item = INPUTS[current]
                        path = choose_path(item, selected.get(item.key))
                        if not path:
                            message = "Cancelled. Previous choices kept."
                            continue
                        path = Path(path).resolve()
                        problem = path_problem(item, path)
                        if problem:
                            message = problem
                            continue
                        selected[item.key] = path
                        message = f"Selected {item.label.lower()}."
                        current = keyboard.next_missing(selected, current)
                except KeyboardInterrupt:
                    message = "All choices kept. Select Exit to leave."
                except (OSError, RuntimeError, ValueError) as error:
                    message = str(error)

    def dates(self, state, mode):
        return choose_dates(state, mode)
