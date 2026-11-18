"""Read selected inputs and reuse the copied planner, messages and checker."""

import copy
import csv
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import yaml

ENGINE = Path(__file__).resolve().parent / "engine"
sys.path.insert(0, str(ENGINE))
import check as checker
import duties
import loader
import main as writer
import schedule
import seat
from engine import validate
from errors import NoPlan

TERMS = ENGINE / "docs" / "terms.md"
OUTPUT = Path(__file__).resolve().parents[1] / "output"


class InputProblem(Exception):
    """Selected files need correction before planning."""


def read_mapping(path):
    try:
        value = loader.read_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise InputProblem(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise InputProblem(f"{path}: expected YAML key/value settings.")
    return value


def read_settings(path):
    settings = read_mapping(path)
    problems = []
    validate.check_settings(settings, problems)
    if problems:
        raise InputProblem(validate.format_report(problems))
    return settings


def source_files(selected):
    paths = [Path(value) for key, value in selected.items() if key != "students"]
    paths.extend(sorted(Path(selected["students"]).glob("*.csv")))
    return paths


def fingerprints(selected):
    return {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source_files(selected)}


def selected_table(path, columns, problems):
    before = len(problems)
    result = validate.check_csv_file(path, path.name, columns, problems)
    if len(problems) != before:
        return []
    header, rows = result
    return [dict(zip(header, values), _row=number) for number, values in rows]


def validate_selection(selected, settings=None):
    """Read the chosen files. Run rules as soon as their inputs are present."""
    data = {}
    problems = []
    for key, value in selected.items():
        path = Path(value)
        try:
            if key in ("settings", "constraints"):
                data[key] = read_mapping(path)
            elif key == "students":
                if not path.is_dir():
                    raise InputProblem(f"{path}: student lists folder is missing.")
                rosters = sorted(path.glob("*.csv"))
                if not rosters:
                    raise InputProblem(f"{path}: student lists folder contains no CSV files.")
                data["roster_files"] = [roster.stem for roster in rosters]
                data["students"] = []
                for roster in rosters:
                    for row in selected_table(roster, loader.ROSTER_COLUMNS, problems):
                        row.update(section_id=roster.stem, _file=str(roster))
                        data["students"].append(row)
            else:
                data[key] = selected_table(path, loader.CSV_COLUMNS[f"{key}.csv"], problems)
        except (InputProblem, OSError, UnicodeError, csv.Error) as error:
            raise InputProblem(f"Stage 1 - file structure\n{error}") from error
    if problems:
        raise InputProblem("Stage 1 - file structure\n" + validate.format_report(problems))

    problems = validate.check_data(data)
    for problem in problems:
        key = Path(problem.file).stem
        if problem.file in loader.CSV_COLUMNS or problem.file in loader.YAML_FILES:
            problem.file = Path(selected[key]).name
    if problems:
        raise InputProblem("Stage 2 - data rules\n" + validate.format_report(problems))
    if settings is not None:
        validate.check_settings(settings, problems)
        if problems:
            raise InputProblem("Stage 2 - calendar settings\n" + validate.format_report(problems))
        data["settings"] = copy.deepcopy(settings)
    # These values become directory/file names when exporting the plan.
    names = [str(value) for value in data.get("settings", {}).get("sessions", [])]
    names.extend(row["room_id"] for row in data.get("rooms", []))
    for name in names:
        if (not name or name in (".", "..") or name[-1:] in (".", " ")
                or any(char in name for char in '<>:"/\\|?*')
                or any(ord(char) < 32 for char in name)
                or name.split(".")[0].upper() in
                {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                 *[f"LPT{i}" for i in range(1, 10)]}):
            raise InputProblem(f"Stage 2 - data rules\nRoom IDs and session names must be safe file names: {name!r}.")
    return data


def load_selected(selected, settings):
    """Generation requires every input, including the effective calendar settings."""
    required = [Path(name).stem for name in loader.CSV_COLUMNS] + ["students", "settings", "constraints"]
    for key in required:
        if key not in selected:
            raise InputProblem(f"Select the {key} input first.")
    return validate_selection(selected, settings)


def checker_input(selected, settings):
    """Re-read selected files using checker readers, independently of loader."""
    read = checker.read_input_table
    groups = checker.read_input_yaml(Path(selected["constraints"])).get("same_paper") or []
    paper_of = {str(code): str(group[0]) for group in groups for code in group}
    codes = {}
    for row in read(Path(selected["courses"]), ["course_code"]):
        code = row["course_code"]
        paper = paper_of.setdefault(code, code)
        codes.setdefault(paper, []).append(code)
    students = {paper: set() for paper in codes}
    for row in read(Path(selected["registrations"]), ["student_id", "course_code"]):
        students[paper_of[row["course_code"]]].add(row["student_id"])
    sections = {}
    for path in sorted(Path(selected["students"]).glob("*.csv")):
        for row in read(path, ["student_id"]):
            sections[row["student_id"]] = path.stem
    rooms = {row["room_id"]: (int(row["rows"]), int(row["seat_columns"]))
             for row in read(Path(selected["rooms"]), ["room_id", "rows", "seat_columns"])}
    ranks = {row["teacher_id"]: row["rank"]
             for row in read(Path(selected["teachers"]), ["teacher_id", "rank"])}
    teaches = {}
    for row in read(Path(selected["teaching"]), ["teacher_id", "course_code", "section_id"]):
        teaches.setdefault(row["teacher_id"], set()).add(
            (paper_of[row["course_code"]], row["section_id"]))
    return dict(start=checker.to_date(settings["start_date"]),
                end=checker.to_date(settings["end_date"]),
                weekdays=set(settings["exam_weekdays"]),
                holidays={checker.to_date(d) for d in (settings["holidays"] or [])},
                sessions=[str(s) for s in settings["sessions"]], gap=settings["min_gap_days"],
                per_room=settings["invigilators_per_room"], codes_of_paper=codes,
                students_of_paper=students, section_of=sections, rooms=rooms,
                room_order=list(rooms), rank_of=ranks, teaches=teaches)


def fresh_folder(output_root=OUTPUT):
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=datetime.now().strftime("%Y-%m-%d_%H-%M-%S_"), dir=root))


def save_failure(reason, output_root=OUTPUT):
    folder = fresh_folder(output_root)
    with (folder / "why.txt").open("x", encoding="utf-8") as stream:
        stream.write(str(reason).rstrip() + "\n")
    return folder / "why.txt"


def recovery_for(reason):
    rule = next((line.removeprefix("Rule: ").strip() for line in str(reason).splitlines()
                 if line.startswith("Rule: ")), "")
    return "dates" if rule in ("gap", "exam days") else "choose"


@dataclass
class Plan:
    folder: Path
    placements: list
    seating: dict
    duty_rows: list
    check_data: dict
    basis: str


def write_basis(folder, basis):
    with (folder / "basis.txt").open("x", encoding="utf-8") as stream:
        stream.write(basis + "\n" + writer.TERMS_LINE + "\n")
    with (folder / "terms.md").open("xb") as stream:
        stream.write(TERMS.read_bytes())


def generate_timetable(selected, settings, output_root=OUTPUT):
    """Compute all feasibility checks, then publish only the checked timetable."""
    try:
        before = fingerprints(selected)
    except OSError as error:
        raise InputProblem(f"An input file cannot be read: {error}") from error
    data = load_selected(selected, settings)
    report = {}
    placements = schedule.make_schedule(data, report)
    if not placements:
        raise NoPlan("No plan possible.\nRule: papers\nThere are no papers to schedule.")
    seating = seat.make_seating(placements, data["rooms"], duties.section_of_student(data),
                                schedule.room_check_for(data))
    duty_rows = duties.make_duties(seating, data, schedule.build_papers(data))
    independent = checker_input(selected, settings)
    if fingerprints(selected) != before:
        raise InputProblem("An input file changed during planning. Review inputs and retry.")
    folder = fresh_folder(output_root)
    timetable = folder / "timetable"
    timetable.mkdir()
    basis = schedule.basis_line(report) + "\n" + seat.basis_line(seating)
    try:
        with (folder / "settings.yaml").open("x", encoding="utf-8") as stream:
            yaml.safe_dump(settings, stream, sort_keys=False)
        with (folder / "sources.json").open("x", encoding="utf-8") as stream:
            json.dump({"paths": {k: str(Path(v).resolve()) for k, v in selected.items()},
                       "sha256": before}, stream, indent=2)
        writer.write_schedule(placements, timetable / "schedule.csv")
        write_basis(timetable, basis)
        problems = checker.Problems()
        rows = checker.read_plan_table(timetable, "schedule.csv", checker.SCHEDULE_COLUMNS,
                                       independent["sessions"], problems)
        if not problems.count():
            slots, _, _ = checker.check_date_sheet(rows, independent, problems)
            for text in checker.check_gap(independent, slots, set()):
                problems.add("gap", text)
        if problems.count():
            raise RuntimeError("Timetable check failed:\n" + problems.report())
    except Exception as error:
        with (folder / "INCOMPLETE.txt").open("x", encoding="utf-8") as stream:
            stream.write(f"Do not use this incomplete output.\n{error}\n")
        raise RuntimeError(f"Could not publish a checked timetable. Details: {folder / 'INCOMPLETE.txt'}\n{error}") from error
    return Plan(folder, placements, seating, duty_rows, independent, basis)


def generate_seating(plan):
    """Export the cached plan after Yes; never recalculate from changed inputs."""
    folder = Path(tempfile.mkdtemp(prefix="seating_", dir=plan.folder))
    try:
        writer.write_schedule(plan.placements, folder / "schedule.csv")
        writer.write_seating(plan.seating, folder)
        writer.write_duties(plan.duty_rows, folder / "duties.csv")
        write_basis(folder, plan.basis)
        problems, numbers = checker.check_plan(plan.check_data, folder)
        if problems.count():
            raise RuntimeError("Plan check failed:\n" + problems.report())
    except Exception as error:
        with (folder / "INCOMPLETE.txt").open("x", encoding="utf-8") as stream:
            stream.write(f"Do not use this incomplete output.\n{error}\n")
        raise RuntimeError(f"Could not publish a checked seating plan: {folder}\n{error}") from error
    return folder, numbers
