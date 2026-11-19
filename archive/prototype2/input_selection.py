"""Select existing exam input files without changing or copying them."""

from dataclasses import dataclass
from pathlib import Path


MAIN_DATA = Path(__file__).resolve().parents[1] / "prototype1" / "data" / "main"


@dataclass(frozen=True)
class InputItem:
    key: str
    label: str
    suffixes: tuple[str, ...]  # Empty means a folder, not a file.


INPUTS = (
    InputItem("teachers", "Teachers", (".csv",)),
    InputItem("courses", "Courses", (".csv",)),
    InputItem("sections", "Section information", (".csv",)),
    InputItem("students", "Student lists folder", ()),
    InputItem("registrations", "Student course registrations", (".csv",)),
    InputItem("rooms", "Rooms", (".csv",)),
    InputItem("teaching", "Teaching assignments", (".csv",)),
    InputItem("settings", "Exam settings", (".yaml", ".yml")),
    InputItem("constraints", "Shared-paper rules", (".yaml", ".yml")),
)


def choose_path(item, previous=None):
    """Open a native file/folder picker. Return None on Cancel."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as error:
        raise RuntimeError("This Python installation needs Tkinter to open pickers.") from error

    root = None
    try:
        root = tk.Tk()
        root.withdraw()  # Only the picker should be visible.
        initial = previous if previous and not item.suffixes else (
            previous.parent if previous else MAIN_DATA)
        options = {"parent": root, "title": f"Select {item.label.lower()}",
                   "initialdir": str(initial)}
        if item.suffixes:
            patterns = " ".join(f"*{suffix}" for suffix in item.suffixes)
            options["filetypes"] = [("Input files", patterns), ("All files", "*")]
            if previous:
                options["initialfile"] = previous.name
            selected = filedialog.askopenfilename(**options)
        else:
            selected = filedialog.askdirectory(mustexist=True, **options)
        return Path(selected) if selected else None
    except tk.TclError as error:
        raise RuntimeError(f"Could not open the picker: {error}") from error
    finally:
        if root is not None:
            root.destroy()


def path_problem(item, path):
    """Check path usability only; data-content validation is a later step."""
    try:
        if not item.suffixes:
            if not path.is_dir():
                return "Select a folder containing the student-section CSV files."
            if not any(child.is_file() and child.suffix.lower() == ".csv"
                       for child in path.iterdir()):
                return "This folder contains no CSV files. Select the student lists folder."
        else:
            if not path.is_file():
                return "The selected file does not exist or is not a regular file."
            if path.suffix.lower() not in item.suffixes:
                return f"Select a file ending in {' or '.join(item.suffixes)}."
            with path.open("rb") as stream:
                if not stream.read(1):
                    return "The selected file is empty. Select a file containing data."
    except OSError as error:
        return f"Cannot read the selected path: {error}"
    return None


def select_inputs(picker=choose_path, read=input, write=print):
    """Keep selections in memory; Cancel and failed replacements keep them."""
    selected = {}
    write("Exam planner - select inputs")
    write("Choose a number to browse. Cancel returns here and keeps your choices.")
    while True:
        write("")
        for number, item in enumerate(INPUTS, start=1):
            write(f"{number}. {item.label}: {selected.get(item.key, 'Not selected')}")
        try:
            choice = read("Number, done to finish, or q to quit: ").strip().lower()
            if choice == "q":
                write("Input selection closed.")
                return None
            if choice == "done":
                missing = [item.label for item in INPUTS if item.key not in selected]
                if missing:
                    write("Still needed: " + ", ".join(missing))
                    continue
                problems = [(item.label, path_problem(item, selected[item.key]))
                            for item in INPUTS]
                if any(problem for _, problem in problems):
                    for label, problem in problems:
                        if problem:
                            write(f"{label}: {problem}")
                    continue
                write("Input selection complete. Selected paths:")
                for item in INPUTS:
                    write(f"{item.label}: {selected[item.key]}")
                return selected
            if choice not in {str(number) for number in range(1, len(INPUTS) + 1)}:
                write(f"Enter a number from 1 to {len(INPUTS)}, done, or q.")
                continue
            item = INPUTS[int(choice) - 1]
            path = picker(item, selected.get(item.key))
            if not path:
                write("Back to inputs. All previous selections are kept.")
                continue
            path = Path(path).resolve()
            problem = path_problem(item, path)
            if problem:
                write(f"{item.label}: {problem} Previous selections are kept.")
                continue
            selected[item.key] = path
            write(f"Selected {item.label.lower()}: {path}")
        except KeyboardInterrupt:
            write("\nBack to inputs. All previous selections are kept. Enter q to quit.")
        except EOFError:
            write("\nTerminal input closed; ending input selection.")
            return None
        except (OSError, RuntimeError) as error:
            write(f"{error} Previous selections are kept; retry or choose another input.")


if __name__ == "__main__":
    select_inputs()
