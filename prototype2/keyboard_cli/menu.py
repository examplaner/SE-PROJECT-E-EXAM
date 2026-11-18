"""Arrow-key input selection for an interactive Windows terminal."""

import ctypes
import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path

# Reuse the previous step without modifying its source file.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from input_selection import INPUTS, choose_path, path_problem


def read_key(read_character=None):
    """Translate Windows key codes into menu actions; no Enter needed to move."""
    if read_character is None:
        import msvcrt
        read_character = msvcrt.getwch
    character = read_character()
    if character in ("\x00", "\xe0"):
        return {"H": "up", "P": "down", "S": "delete"}.get(read_character(), "ignore")
    return {"\r": "enter", "\n": "enter", "\x1b": "back",
            "\x03": "back"}.get(character, "ignore")


def next_missing(selected, current):
    """Find the next unselected input, wrapping around; otherwise Continue."""
    for offset in range(1, len(INPUTS) + 1):
        index = (current + offset) % len(INPUTS)
        if INPUTS[index].key not in selected:
            return index
    return len(INPUTS)


def select_inputs(get_key, draw, picker=choose_path, check_path=path_problem):
    """Run the menu. Selection changes stay in memory, never in input files."""
    selected = {}
    current = 0
    message = "Choose an input and press Enter."
    while True:
        draw(selected, current, message)
        try:
            action = get_key()
            if action in ("up", "down"):
                current = (current + (1 if action == "down" else -1)) % (len(INPUTS) + 2)
            elif action == "back":
                message = "Back to inputs. All selections kept. Select Exit to leave."
            elif action == "delete":
                if current < len(INPUTS):
                    item = INPUTS[current]
                    selected.pop(item.key, None)
                    message = f"{item.label} cleared. No file was deleted."
                else:
                    message = "Highlight an input to clear its selection."
            elif action == "enter":
                if current == len(INPUTS) + 1:
                    return None
                if current == len(INPUTS):
                    for index, item in enumerate(INPUTS):
                        problem = (check_path(item, selected[item.key])
                                   if item.key in selected else "Select this input first.")
                        if problem:
                            current = index
                            message = f"{item.label}: {problem}"
                            break
                    else:
                        return selected
                    continue
                item = INPUTS[current]
                path = picker(item, selected.get(item.key))
                if not path:
                    message = "Cancelled. All previous selections kept."
                    continue
                path = Path(path).resolve()
                problem = check_path(item, path)
                if problem:
                    message = f"{problem} Previous selections kept."
                    continue
                selected[item.key] = path
                message = f"Selected {item.label.lower()}."
                current = next_missing(selected, current)
        except KeyboardInterrupt:
            message = "Back to inputs. All selections kept. Select Exit to leave."
        except (OSError, RuntimeError, ValueError) as error:
            message = f"{error} Previous selections kept."
        except EOFError:
            return None


@contextmanager
def terminal_screen():
    """Enable Windows terminal drawing and restore the console on exit."""
    if os.name != "nt" or not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError("Run this menu in an interactive Windows terminal.")
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetConsoleMode.restype = wintypes.BOOL
    kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.SetConsoleMode.restype = wintypes.BOOL
    handle = kernel.GetStdHandle(-11)  # Standard output handle.
    original_mode = wintypes.DWORD()
    if not kernel.GetConsoleMode(handle, ctypes.byref(original_mode)):
        raise RuntimeError("This terminal does not provide a Windows console.")
    if not kernel.SetConsoleMode(handle, original_mode.value | 0x0004):
        raise RuntimeError("This terminal cannot enable arrow-menu drawing.")
    try:
        # Use a separate screen so the previous terminal contents remain intact.
        sys.stdout.write("\x1b[?1049h\x1b[?25l\x1b[2J\x1b[H")
        sys.stdout.flush()
        yield
    finally:
        try:
            sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            sys.stdout.flush()
        finally:
            kernel.SetConsoleMode(handle, original_mode.value)


def draw_menu(selected, current, message):
    """Redraw in place; keep the highlighted row visible in smaller terminals."""
    columns, rows = shutil.get_terminal_size((100, 30))
    width = max(1, columns - 1)
    encoding = sys.stdout.encoding or "utf-8"
    try:
        "\u2713".encode(encoding)
        tick = "\u2713"
    except (LookupError, UnicodeEncodeError):
        tick = "x"

    lines = ["Exam planner - select inputs",
             "Up/Down Move | Enter Select/Replace | Delete Clear", ""]
    entries = []
    for item in INPUTS:
        path = selected.get(item.key)
        status = f"[{tick}]" if path else "[ ]"
        entries.append(f"{status} {item.label}: {path.name if path else 'Not selected'}")
    entries.extend(["Continue", "Exit"])
    visible = max(1, rows - 7)
    start = max(0, min(current - visible + 1, len(entries) - visible))
    for index in range(start, min(len(entries), start + visible)):
        text = ("> " if index == current else "  ") + entries[index]
        text = text[:width]
        if index == current:
            text = "\x1b[7m" + text + "\x1b[0m"
        lines.append(text)
    lines += ["", message[:width]]
    if current < len(INPUTS) and INPUTS[current].key in selected:
        lines.append(str(selected[INPUTS[current].key])[:width])
    # Clear the remainder of each line and screen after drawing shorter text.
    output = "\x1b[H" + "\n".join(
        (line if "\x1b[7m" in line else line[:width]) + "\x1b[K"
        for line in lines) + "\x1b[J"
    sys.stdout.write(output)
    sys.stdout.flush()


def main():
    try:
        with terminal_screen():
            selected = select_inputs(read_key, draw_menu)
    except (OSError, RuntimeError) as error:
        print(error)
        return 1
    if selected is None:
        print("Input selection closed.")
    else:
        print("Input selection complete:")
        for item in INPUTS:
            print(f"{item.label}: {selected[item.key]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
