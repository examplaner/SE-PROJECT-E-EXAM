"""Choosing the nine inputs with Tkinter file and folder pickers, never by
typing a path.

Choices live only in memory while the app runs. Cancel in a picker keeps the
old choice, clearing a choice never touches its file, and no input file is
ever written.
"""

from dataclasses import dataclass
from pathlib import Path

# where the pickers start browsing
EXAMPLE_DATA = Path(__file__).resolve().parent / "data" / "realistic_example"


@dataclass(frozen=True)
class Input:
    # the name the engine's loader.input_paths() uses for it
    key: str
    label: str
    # the file endings it may have; empty for a folder
    suffixes: tuple


INPUTS = [
    Input("teachers", "Teachers", (".csv",)),
    Input("courses", "Courses", (".csv",)),
    Input("sections", "Section information", (".csv",)),
    Input("students", "Student lists folder", ()),
    Input("registrations", "Student course registrations", (".csv",)),
    Input("rooms", "Rooms", (".csv",)),
    Input("teaching", "Who teaches what", (".csv",)),
    Input("settings", "Exam settings", (".yaml", ".yml")),
    Input("constraints", "Shared-paper rules", (".yaml", ".yml")),
]


def pick_inputs(selected, ask, pick, check, show):
    """The inputs menu. selected: {key: Path}, changed in place, so going back
    to this menu never loses a choice. ask(message, choices, default) shows a
    menu of (title, value, description) choices and returns the value chosen,
    or None after Ctrl+C. pick(item, previous) opens a picker and returns a
    path, or None on Cancel; it is choose_path() in the app. check(item,
    path) gives a problem or None; it is path_problem() in the app. show
    prints a message. Returns True to go on to the exam dates, False to exit."""
    current = next_missing(selected, len(INPUTS) - 1)
    show("Choose each input. Your choices stay selected when you come back here.")
    while True:
        answer = ask("Exam planner - inputs", menu_choices(selected), current)
        if answer is None:
            show("All choices kept. Choose Exit if you want to leave.")
        elif answer == "exit":
            return False
        elif answer == "continue":
            missing = first_problem(selected, check)
            if missing is None:
                return True
            current, problem = missing
            show(f"{INPUTS[current].label}: {problem}")
        elif answer == "clear":
            current = clear_a_choice(selected, ask, show, current)
        else:
            current = choose_one(answer, selected, pick, check, show)


def menu_choices(selected):
    """The rows of the inputs menu: each input with the file chosen for it,
    then the actions. The full path shows under the highlighted input."""
    choices = []
    for index, item in enumerate(INPUTS):
        if item.key in selected:
            path = selected[item.key]
            choices.append((f"[x] {item.label}: {path.name}", index, str(path)))
        else:
            choices.append((f"[ ] {item.label}: not chosen", index, None))
    choices.append(("Clear a choice", "clear", "The file itself is never touched."))
    choices.append(("Continue to exam dates", "continue", None))
    choices.append(("Exit", "exit", None))
    return choices


def choose_one(index, selected, pick, check, show):
    """Open the picker for one input. Returns the row to highlight next: the
    next input still missing, or the same row if nothing changed."""
    item = INPUTS[index]
    try:
        path = pick(item, selected.get(item.key))
    except (OSError, RuntimeError) as error:
        show(f"{error} Previous choices kept.")
        return index
    if path is None:
        show("Cancelled. Previous choices kept.")
        return index
    path = Path(path).resolve()
    problem = check(item, path)
    if problem:
        show(f"{problem} Previous choices kept.")
        return index
    selected[item.key] = path
    show(f"Chose {item.label.lower()}: {path}")
    return next_missing(selected, index)


def clear_a_choice(selected, ask, show, current):
    """Ask which choice to clear. Returns the row to highlight next: the
    cleared input, so its new file can be chosen straight away."""
    choices = []
    for index, item in enumerate(INPUTS):
        if item.key in selected:
            choices.append((f"{item.label}: {selected[item.key].name}", index, None))
    if not choices:
        show("Nothing is chosen yet.")
        return current
    choices.append(("Back", "back", None))
    answer = ask("Clear which choice? Its file is not touched.", choices, choices[0][1])
    if answer is None or answer == "back":
        return current
    item = INPUTS[answer]
    del selected[item.key]
    show(f"{item.label} cleared. No file was deleted.")
    return answer


def next_missing(selected, after):
    """The index of the next input not chosen yet after `after`, going round
    to the start; "continue" when every input is chosen."""
    for step in range(1, len(INPUTS) + 1):
        index = (after + step) % len(INPUTS)
        if INPUTS[index].key not in selected:
            return index
    return "continue"


def first_problem(selected, check):
    """(index, problem) of the first input that is missing or no longer
    usable, or None when every input is ready. Paths are checked again, as a
    file may have changed since it was chosen."""
    for index, item in enumerate(INPUTS):
        if item.key not in selected:
            return index, "Choose this input first."
        problem = check(item, selected[item.key])
        if problem:
            return index, problem
    return None


def path_problem(item, path):
    """Whether a chosen path can be used, or None. The data inside is checked
    later, by the engine."""
    try:
        if not item.suffixes:
            if not path.is_dir():
                return "Choose a folder holding the student-section CSV files."
            has_csv = False
            for child in path.iterdir():
                if child.is_file() and child.suffix.lower() == ".csv":
                    has_csv = True
            if not has_csv:
                return "This folder holds no CSV files. Choose the student lists folder."
            return None
        if not path.is_file():
            return "The chosen file does not exist or is not a regular file."
        if path.suffix.lower() not in item.suffixes:
            return f"Choose a file ending in {' or '.join(item.suffixes)}."
        with path.open("rb") as file:
            if not file.read(1):
                return "The chosen file is empty. Choose a file with data in it."
    except OSError as error:
        return f"Can't read the chosen path: {error}"
    return None


def choose_path(item, previous=None):
    """Open a Tkinter file or folder picker. Returns the path, or None on
    Cancel."""
    # imported here, so the rest of the app and its tests work without Tkinter
    try:
        import tkinter
        from tkinter import filedialog
    except ImportError as error:
        raise RuntimeError("This Python has no Tkinter, so it can't open pickers.") from error

    if previous is None:
        start = EXAMPLE_DATA
    elif item.suffixes:
        start = previous.parent
    else:
        start = previous

    root = None
    try:
        root = tkinter.Tk()
        # only the picker should show, not an empty main window
        root.withdraw()
        title = f"Choose {item.label.lower()}"
        if item.suffixes:
            patterns = " ".join(f"*{suffix}" for suffix in item.suffixes)
            chosen = filedialog.askopenfilename(
                parent=root, title=title, initialdir=str(start),
                initialfile=previous.name if previous else "",
                filetypes=[("Input files", patterns), ("All files", "*")])
        else:
            chosen = filedialog.askdirectory(parent=root, title=title, initialdir=str(start),
                                             mustexist=True)
    except tkinter.TclError as error:
        raise RuntimeError(f"Could not open the picker: {error}") from error
    finally:
        if root is not None:
            root.destroy()
    if chosen:
        return Path(chosen)
    return None
