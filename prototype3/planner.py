"""Runs the planner in engine/ on the files picked in the app, and writes each
run into a new folder under prototype3/output/. Input files are only read.

A run makes the whole plan (timetable, seating, duties) before it writes
anything, so a timetable is only shown if seats and teachers work out too.
The timetable is written first; the seating and duties only after the second
yes. Each part is checked by the engine's own checker before it is shown.
"""

import json
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

ENGINE = Path(__file__).resolve().parent / "engine"
# the engine's modules import each other by name, so its folder goes on the path
sys.path.insert(0, str(ENGINE))
import check  # noqa: E402
import duties  # noqa: E402
import loader  # noqa: E402
import schedule  # noqa: E402
import seat  # noqa: E402
import validate  # noqa: E402
import writer  # noqa: E402
from errors import NoPlan  # noqa: E402
from exam import build_exam  # noqa: E402

TERMS = ENGINE / "terms.md"
OUTPUT = Path(__file__).resolve().parent / "output"
# names Windows keeps for devices; a room or session can't be called that,
# because it becomes a file or folder name
RESERVED_NAMES = ["CON", "PRN", "AUX", "NUL"]
for number in range(1, 10):
    RESERVED_NAMES += [f"COM{number}", f"LPT{number}"]


class InputProblem(Exception):
    """The picked files need fixing before a plan can be made."""


@dataclass
class Plan:
    # the run's folder; the timetable is in its timetable/ folder
    folder: Path
    placements: list
    seating: dict
    duty_rows: list
    basis: list
    # what the checker read from the inputs, kept so the seating is checked
    # against the same inputs as the timetable
    check_data: dict


def read_settings(path):
    """The picked settings file, checked. Raises InputProblem."""
    problems = []
    try:
        validate.check_yaml_file(Path(path), problems)
        if problems:
            raise InputProblem(validate.format_report(problems))
        settings = loader.read_yaml(path)
    except OSError as error:
        raise InputProblem(f"{path}: {error}") from error
    validate.check_settings(settings, problems)
    if problems:
        raise InputProblem(validate.format_report(problems))
    return settings


def file_problem(key, path):
    """The problems of one picked input on its own, as a report, or None. The
    file must be readable with the right header; rooms, teachers and settings
    must also pass the data rules that need no other file. The rules across
    files run in load_selected(), once every input is chosen."""
    problems = []
    try:
        if key == "students":
            for roster in loader.roster_paths(path):
                validate.check_csv_file(roster, f"{path.name}/{roster.name}",
                                        loader.ROSTER_COLUMNS, problems)
        elif key in ("settings", "constraints"):
            validate.check_yaml_file(path, problems)
        else:
            validate.check_csv_file(path, path.name, loader.CSV_COLUMNS[key], problems)

        if not problems:
            if key == "rooms":
                validate.check_rooms({"rooms": loader.read_table(path)}, problems)
            elif key == "teachers":
                validate.check_teachers({"teachers": loader.read_table(path)}, problems)
            elif key == "settings":
                validate.check_settings(loader.read_yaml(path), problems)
    except OSError as error:
        return f"{path.name} can't be read: {error}"
    if not problems:
        return None
    name_picked_files(problems, {key: path})
    return validate.format_report(problems)


def name_picked_files(problems, selected):
    """The checks name each input by its usual file name, such as
    registrations.csv; change that to the name of the file that was picked."""
    # only the file names are used, so the folder doesn't matter
    usual_paths = loader.input_paths(".")
    picked_name = {}
    for key, path in selected.items():
        if key != "students":
            picked_name[usual_paths[key].name] = Path(path).name
    for problem in problems:
        if problem.file in picked_name:
            problem.file = picked_name[problem.file]


def load_selected(selected, settings):
    """Read and check the picked files with the engine's own checks. selected
    uses the same keys as loader.input_paths(); settings are the settings
    file's, or this run's from the calendars. Raises InputProblem."""
    try:
        problems = validate.check_files(selected)
        if problems:
            raise InputProblem(validate.format_report(problems))
        data = loader.load(selected)
    except OSError as error:
        raise InputProblem(f"An input file can't be read: {error}") from error
    data["settings"] = settings
    problems = validate.check_data(data)
    if problems:
        name_picked_files(problems, selected)
        raise InputProblem(validate.format_report(problems))

    # room IDs and session names become file and folder names
    names = [str(session) for session in settings["sessions"]]
    names += [room["room_id"] for room in data["rooms"]]
    for name in names:
        if not is_safe_file_name(name):
            raise InputProblem(f"Room IDs and session names must be safe file names: {name!r}.")
    return data


def is_safe_file_name(name):
    """A name that works as a file name on Windows, Linux and Mac."""
    if name in ("", ".", "..") or name.endswith(".") or name.endswith(" "):
        return False
    for character in name:
        # characters Windows forbids in a name, and control characters
        if character in '<>:"/\\|?*' or ord(character) < 32:
            return False
    return name.split(".")[0].upper() not in RESERVED_NAMES


def generate_timetable(selected, settings, output_root=OUTPUT):
    """Make the whole plan, then write and check only the timetable. Returns a
    Plan. Raises NoPlan, InputProblem, or RuntimeError if the timetable could
    not be written and checked."""
    exam = build_exam(load_selected(selected, settings))
    placements, way, failed = schedule.make_schedule(exam)
    if not placements:
        raise NoPlan("No plan possible.\nRule: papers\nThere are no papers to schedule.")
    seating = seat.make_seating(placements, exam)
    duty_rows = duties.make_duties(seating, exam)
    basis = [schedule.basis_line(way, failed), seat.basis_line(seating)]

    folder = new_run_folder(output_root)
    try:
        # this run's settings and the files it was made from, beside the plan
        with open(folder / "settings.yaml", "x", encoding="utf-8") as file:
            yaml.safe_dump(settings, file, sort_keys=False)
        sources = {key: str(Path(path).resolve()) for key, path in selected.items()}
        with open(folder / "sources.json", "x", encoding="utf-8") as file:
            json.dump(sources, file, indent=2)

        timetable = folder / "timetable"
        timetable.mkdir()
        writer.write_schedule(placements, timetable / "schedule.csv")
        writer.write_basis(basis, timetable)
        # the checker reads the inputs with its own code, and this run's
        # settings from the copy just written
        check_paths = dict(selected)
        check_paths["settings"] = folder / "settings.yaml"
        check_data = check.load_input(check_paths)
        check_timetable(check_data, timetable)
    except Exception as error:
        mark_incomplete(folder, error)
        raise RuntimeError(f"Could not save a checked timetable. Details: "
                           f"{folder / 'INCOMPLETE.txt'}\n{error}") from error
    return Plan(folder, placements, seating, duty_rows, basis, check_data)


def check_timetable(check_data, timetable):
    """The checker's date sheet rules and the gap rule, on schedule.csv only.
    Raises RuntimeError if a rule is broken."""
    problems = check.Problems()
    rows = check.read_plan_table(timetable, "schedule.csv", check.SCHEDULE_COLUMNS,
                                 check_data["sessions"], problems)
    if not problems.count():
        slot_of, _, _ = check.check_date_sheet(rows, check_data, problems)
        check.check_gap(check_data, slot_of, set(), problems)
    if problems.count():
        raise RuntimeError("Timetable check failed:\n" + problems.report())


def generate_seating(plan):
    """Write the seating plan and duties already made with the timetable, in a
    new seating_* folder inside the run's folder, and check the whole plan.
    Returns (folder, the checker's numbers)."""
    folder = Path(tempfile.mkdtemp(prefix="seating_", dir=plan.folder))
    try:
        writer.write_schedule(plan.placements, folder / "schedule.csv")
        writer.write_seating(plan.seating, folder)
        writer.write_duties(plan.duty_rows, folder / "duties.csv")
        writer.write_basis(plan.basis, folder)
        problems, numbers = check.check_plan(plan.check_data, folder)
        if problems.count():
            raise RuntimeError("Plan check failed:\n" + problems.report())
    except Exception as error:
        mark_incomplete(folder, error)
        raise RuntimeError(f"Could not save a checked seating plan: {folder}\n{error}") from error
    return folder, numbers


def save_failure(reason, output_root=OUTPUT):
    """why.txt with the engine's reason, alone in a new folder. Returns its path."""
    folder = new_run_folder(output_root)
    with open(folder / "why.txt", "x", encoding="utf-8") as file:
        file.write(str(reason).rstrip() + "\n")
    return folder / "why.txt"


def recovery_for(reason):
    """Returns "dates" when other exam dates can fix the reason, else "choose"."""
    for line in str(reason).splitlines():
        if line.startswith("Rule: "):
            rule = line[len("Rule: "):].strip()
            if rule in ("gap", "exam days"):
                return "dates"
            return "choose"
    return "choose"


def new_run_folder(output_root):
    """A new folder named by the time, with a random ending so two runs in
    one second never share a folder and nothing is overwritten."""
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_")
    return Path(tempfile.mkdtemp(prefix=stamp, dir=root))


def mark_incomplete(folder, error):
    """Leave a note, so a half-written folder is never taken for a plan."""
    with open(folder / "INCOMPLETE.txt", "x", encoding="utf-8") as file:
        file.write(f"Do not use this incomplete output.\n{error}\n")
