"""Check a plan folder against every yes/no rule of the spec (model spec
sections 13 and 14). It never writes a file.

    python check.py data/tiny output/<timestamp>

It reads every file with its own code and imports nothing from the planner,
so a bug in the planner can't hide from it. Only yes/no rules are checked;
"try to" rules (one paper per room where possible, one shift a day, PhD
scholars last, biggest paper first, ...) are preferences, not rules.

Each mistake is shown once, as its main issue, without follow-on errors:
  stage 1, files: the plan's files are there, readable and the right shape.
           If anything is broken here, the checker stops.
  stage 2, rows:  each date sheet row, seat and duty row makes sense on its
           own. A bad seat or duty row is reported once and left out of
           stage 3.
  stage 3, rules over many rows: gap, column rule, everyone seated once,
           roll order, teachers per room, ... A paper in a slot, a room, or
           a teacher in a slot is reported at most once, under the first
           rule it breaks.

Exit codes:
    0  the plan is clean
    1  can't check: the input folder or the plan folder can't be read
    2  nothing to check: the folder holds only why.txt (no plan possible)
    3  the plan breaks a rule; every problem is printed under its rule
"""

import argparse
import csv
import datetime
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PHD = "PHD"
SCHEDULE_COLUMNS = ["date", "session", "paper_id", "course_codes", "students"]
DUTY_COLUMNS = ["date", "session", "room_id", "teacher_id"]
SEATING_FOLDER = "daywise_seating_plans"
# basis.txt and terms.md are allowed in a plan folder but not checked, and a
# plan without them is still a plan
PLAN_ITEMS = ["schedule.csv", "duties.csv", SEATING_FOLDER, "basis.txt", "terms.md"]

# every rule the checker knows, in the order problems are printed
RULES = [
    # stage 1: files
    "output files", "room shape", "room cell",
    # stage 2: rows on their own
    "date sheet", "same paper", "exam days", "registration",
    "paper in its slot", "known teacher", "duty in a used room",
    # stage 3: rules over many rows
    "gap", "two papers at most", "one paper per column", "column rule",
    "seated once", "roll order",
    "one duty per slot", "teachers per room", "own students", "own paper duty",
]
STAGE_1_RULES = ["output files", "room shape", "room cell"]


class CannotCheck(Exception):
    """The input folder or the plan folder can't be read (exit 1)."""


class Problems:
    """The problems found so far, by rule."""

    def __init__(self):
        self.by_rule = {rule: [] for rule in RULES}

    def add(self, rule, text):
        self.by_rule[rule].append(text)

    def count(self):
        return sum(len(texts) for texts in self.by_rule.values())

    def report(self):
        broken = [rule for rule in RULES if self.by_rule[rule]]
        lines = [f"Plan check: {self.count()} problem(s), {len(broken)} rule(s) broken."]
        for rule in broken:
            lines.append("")
            lines.append(f"Rule: {rule} ({len(self.by_rule[rule])})")
            for text in self.by_rule[rule]:
                lines.append(f"  {text}")
        return "\n".join(lines)


@dataclass
class RoomFile:
    # path inside the plan folder, for messages
    where: str
    # (date, session)
    slot: tuple
    room_id: str
    # grid[row][column] is (paper_id, student_id), or None for an empty seat
    grid: list


@dataclass
class Seat:
    # e.g. "daywise_seating_plans/2026-11-02/morning/S01.csv row 2, column 1"
    where: str
    slot: tuple
    room_id: str
    row: int
    column: int
    paper_id: str
    student_id: str


def front_row_first(seat):
    """Sort key for Seats."""
    return seat.row


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a plan folder against the rules.")
    parser.add_argument("input_dir", help="the input folder the plan was made from, "
                                          "e.g. data/tiny")
    parser.add_argument("plan_dir", help="a plan folder written by main.py, "
                                         "e.g. output/<timestamp>")
    args = parser.parse_args(argv)

    try:
        if not Path(args.input_dir).is_dir():
            raise CannotCheck(f"the input folder {Path(args.input_dir)} doesn't exist.")
        data = load_input(input_paths(args.input_dir))
        folder = Path(args.plan_dir)
        if not folder.is_dir():
            raise CannotCheck(f"the plan folder {folder} doesn't exist.")
    except CannotCheck as reason:
        print(f"Can't check: {reason}")
        return 1

    why = folder / "why.txt"
    if why.is_file() and not (folder / "schedule.csv").exists():
        print("No plan in this folder, nothing to check. why.txt says:\n")
        print(why.read_text(encoding="utf-8", errors="replace").rstrip())
        return 2

    problems, numbers = check_plan(data, folder)
    if problems.count():
        print(problems.report())
        if any(problems.by_rule[rule] for rule in STAGE_1_RULES):
            print("\nFix these first. The other rules are checked once every "
                  "plan file can be read.")
        return 3
    print(f"Plan check: no problems. {numbers['papers']} papers, "
          f"{numbers['room files']} room files, {numbers['seats']} seats, "
          f"{numbers['duties']} duties checked.")
    return 0


def check_plan(data, folder):
    """All three stages. Returns (Problems, numbers for the summary line)."""
    problems = Problems()
    schedule_rows, duty_rows, room_files = read_plan(folder, data, problems)
    numbers = {"papers": len(schedule_rows), "room files": len(room_files),
               "duties": len(duty_rows)}
    if problems.count():
        return problems, numbers

    # stage 2
    slot_of, row_of, skipped = check_date_sheet(schedule_rows, data, problems)
    good_seats, bad_students, wrong_slot_papers, wrong_student = check_seats_alone(
        room_files, data, slot_of, row_of, skipped, problems)
    # papers whose real slot is not known: the date sheet and the rooms disagree
    doubtful = skipped | wrong_slot_papers
    good_rows, rooms_of_bad_rows = check_duty_rows_alone(duty_rows, data, room_files, problems)

    # stage 3
    check_gap(data, slot_of, doubtful, problems)
    reported = check_rooms(room_files, good_seats, problems)
    check_seated_once(data, slot_of, good_seats, bad_students, wrong_student, reported,
                      problems)
    check_roll_order(data, slot_of, good_seats, reported, problems)
    check_duties(good_rows, rooms_of_bad_rows, room_files, data, slot_of, doubtful,
                 good_seats, problems)
    numbers["seats"] = len(good_seats)
    return problems, numbers


# reading the input folder

def input_paths(input_dir):
    """Where each input lives inside an input folder."""
    folder = Path(input_dir)
    paths = {}
    for key in ["sections", "courses", "registrations", "rooms", "teachers", "teaching"]:
        paths[key] = folder / f"{key}.csv"
    paths["students"] = folder / "sections"
    paths["settings"] = folder / "settings.yaml"
    paths["constraints"] = folder / "constraints.yaml"
    return paths


def read_csv_file(path, skip_blank_lines=True):
    """Every line of a CSV file as (line number, values), values stripped and
    Excel's byte-order mark ignored. Raises OSError, UnicodeDecodeError or
    csv.Error if the file can't be read."""
    lines = []
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        for values in reader:
            values = [value.strip() for value in values]
            if skip_blank_lines and not any(values):
                continue
            lines.append((reader.line_num, values))
    return lines


def read_input_table(path, columns):
    """An input CSV file as row dicts. Raises CannotCheck if it is missing,
    unreadable or lacks one of `columns`."""
    if not path.is_file():
        raise CannotCheck(f"{path} is missing.")
    try:
        lines = read_csv_file(path)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise CannotCheck(f"{path} can't be read ({error}).")
    if not lines:
        raise CannotCheck(f"{path} is empty.")
    _, header = lines[0]
    missing = [column for column in columns if column not in header]
    if missing:
        raise CannotCheck(f"{path} has no column {', '.join(missing)}.")
    return [dict(zip(header, values)) for _, values in lines[1:]]


def read_input_yaml(path):
    if not path.is_file():
        raise CannotCheck(f"{path} is missing.")
    # ValueError: PyYAML reads 2026-11-40 as a date and then fails on it
    try:
        with open(path, encoding="utf-8-sig") as file:
            content = yaml.safe_load(file)
    except (OSError, UnicodeDecodeError, yaml.YAMLError, ValueError) as error:
        raise CannotCheck(f"{path} can't be read ({error}).")
    if content is None:
        return {}
    if not isinstance(content, dict):
        raise CannotCheck(f"{path} should hold keys and values.")
    return content


def to_date(value):
    """A YAML date or 'YYYY-MM-DD' text as a date. Raises ValueError."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def load_input(paths):
    """Everything the checker needs from the input, as one dict. Raises
    CannotCheck if a file can't be read."""
    settings = read_input_yaml(paths["settings"])
    constraints = read_input_yaml(paths["constraints"])
    data = settings_values(settings, paths["settings"])
    paper_of_code = paper_groups(constraints)
    codes_of_paper, students_of_paper = read_papers(paths["courses"], paths["registrations"],
                                                    paper_of_code)
    data["codes_of_paper"] = codes_of_paper
    data["students_of_paper"] = students_of_paper
    data["section_of"] = read_sections(paths["students"])
    data["rooms"], data["room_order"] = read_rooms(paths["rooms"])
    data["rank_of"] = read_ranks(paths["teachers"])
    data["teaches"] = read_teaching(paths["teaching"], paper_of_code)
    return data


def settings_values(settings, path):
    """The settings the checks use. Raises CannotCheck if one is missing or
    wrong."""
    try:
        return {
            "start": to_date(settings["start_date"]),
            "end": to_date(settings["end_date"]),
            "weekdays": {str(day) for day in settings["exam_weekdays"]},
            "holidays": {to_date(day) for day in (settings.get("holidays") or [])},
            "sessions": [str(session) for session in settings["sessions"]],
            "gap": int(settings["min_gap_days"]),
            "per_room": int(settings["invigilators_per_room"]),
        }
    except (KeyError, TypeError, ValueError) as error:
        raise CannotCheck(f"{path} has a missing or wrong value ({error}).")


def paper_groups(constraints):
    """{course_code: paper_id} for the codes in a same_paper group: codes in
    one group are one paper, named by the first code."""
    paper_of_code = {}
    for group in constraints.get("same_paper") or []:
        codes = [str(code) for code in group]
        for code in codes:
            paper_of_code[code] = codes[0]
    return paper_of_code


def read_papers(courses_path, registrations_path, paper_of_code):
    """Returns ({paper_id: its course codes}, {paper_id: its students})."""
    codes_of_paper = {}
    for course in read_input_table(courses_path, ["course_code"]):
        code = course["course_code"]
        paper_id = paper_of_code.get(code, code)
        codes_of_paper.setdefault(paper_id, []).append(code)

    students_of_paper = {paper_id: set() for paper_id in codes_of_paper}
    for row in read_input_table(registrations_path, ["student_id", "course_code"]):
        code = row["course_code"]
        paper_id = paper_of_code.get(code, code)
        students_of_paper.setdefault(paper_id, set()).add(row["student_id"])
        # a registered code missing from courses.csv still counts as a paper,
        # so its seats are checked too
        if paper_id not in codes_of_paper:
            codes_of_paper[paper_id] = [code]
    return codes_of_paper, students_of_paper


def read_sections(students_folder):
    """{student_id: section_id}, from the roster files."""
    section_of = {}
    for path in sorted(Path(students_folder).glob("*.csv")):
        for row in read_input_table(path, ["student_id"]):
            section_of[row["student_id"]] = path.stem
    return section_of


def read_rooms(path):
    """Returns ({room_id: (rows, seat_columns)}, the room IDs in rooms.csv
    order)."""
    rooms = {}
    room_order = []
    for row in read_input_table(path, ["room_id", "rows", "seat_columns"]):
        try:
            rooms[row["room_id"]] = (int(row["rows"]), int(row["seat_columns"]))
        except ValueError:
            raise CannotCheck(f"{path}: room {row['room_id']} has a size that "
                              f"is not a number.")
        room_order.append(row["room_id"])
    return rooms, room_order


def read_ranks(path):
    """{teacher_id: rank}."""
    rank_of = {}
    for row in read_input_table(path, ["teacher_id", "rank"]):
        rank_of[row["teacher_id"]] = row["rank"]
    return rank_of


def read_teaching(path, paper_of_code):
    """{teacher_id: set of (paper_id, section_id)}."""
    teaches = {}
    for row in read_input_table(path, ["teacher_id", "course_code", "section_id"]):
        paper_id = paper_of_code.get(row["course_code"], row["course_code"])
        teaches.setdefault(row["teacher_id"], set()).add((paper_id, row["section_id"]))
    return teaches


# stage 1: the plan's files

def read_plan(folder, data, problems):
    """Returns (schedule rows, duty rows, RoomFiles)."""
    for item in sorted(folder.iterdir()):
        if item.name not in PLAN_ITEMS:
            problems.add("output files",
                         f"{item.name}: a plan folder holds only schedule.csv, duties.csv, "
                         f"basis.txt, terms.md and {SEATING_FOLDER}/.")
    schedule_rows = read_plan_table(folder, "schedule.csv", SCHEDULE_COLUMNS,
                                    data["sessions"], problems)
    duty_rows = read_plan_table(folder, "duties.csv", DUTY_COLUMNS, data["sessions"], problems)
    room_files = read_seating(folder, data, problems)
    return schedule_rows, duty_rows, room_files


def read_plan_table(folder, name, columns, sessions, problems):
    """schedule.csv or duties.csv as row dicts, with "_row" (line number,
    header = row 1) and "_day". A row with a wrong date, session or number of
    values is reported and left out."""
    path = folder / name
    if not path.is_file():
        problems.add("output files", f"{name} is missing.")
        return []
    try:
        lines = read_csv_file(path)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        problems.add("output files", f"{name} can't be read ({error}).")
        return []
    header = []
    if lines:
        _, header = lines[0]
    if header != columns:
        problems.add("output files", f"{name}: the header should be {','.join(columns)}.")
        return []

    rows = []
    for line, values in lines[1:]:
        where = f"{name} row {line}"
        if len(values) != len(columns):
            problems.add("output files",
                         f"{where}: {len(values)} values, should be {len(columns)}.")
            continue
        row = dict(zip(columns, values), _row=line)
        try:
            row["_day"] = datetime.date.fromisoformat(row["date"])
        except ValueError:
            problems.add("output files",
                         f"{where}: '{row['date']}' is not a date (YYYY-MM-DD).")
            continue
        if row["session"] not in sessions:
            problems.add("output files", f"{where}: '{row['session']}' is not a session "
                                         f"({', '.join(sessions)}).")
            continue
        rows.append(row)
    return rows


def read_seating(folder, data, problems):
    """Every room CSV in daywise_seating_plans/<date>/<session>/, as RoomFiles."""
    seating_folder = folder / SEATING_FOLDER
    if not seating_folder.is_dir():
        problems.add("output files", f"{SEATING_FOLDER}/ is missing.")
        return []

    room_files = []
    for day_folder in sorted(seating_folder.iterdir()):
        name = f"{SEATING_FOLDER}/{day_folder.name}"
        try:
            day = datetime.date.fromisoformat(day_folder.name)
        except ValueError:
            problems.add("output files",
                         f"{name}: should be a folder named by a date (YYYY-MM-DD).")
            continue
        if not day_folder.is_dir():
            problems.add("output files", f"{name}: should be a folder.")
            continue
        for session_folder in sorted(day_folder.iterdir()):
            name = f"{SEATING_FOLDER}/{day_folder.name}/{session_folder.name}"
            if not session_folder.is_dir() or session_folder.name not in data["sessions"]:
                problems.add("output files", f"{name}: should be a session folder "
                                             f"({', '.join(data['sessions'])}).")
                continue
            for path in sorted(session_folder.iterdir()):
                where = f"{name}/{path.name}"
                room_id = path.stem
                if path.suffix != ".csv" or room_id not in data["rooms"]:
                    problems.add("output files",
                                 f"{where}: not a room CSV of a room in rooms.csv.")
                    continue
                grid = read_room_file(path, where, data["rooms"][room_id], problems)
                if grid is not None:
                    room_files.append(RoomFile(where, (day, session_folder.name), room_id, grid))
    return room_files


def read_room_file(path, where, size, problems):
    """One room CSV as a grid. Returns None (and reports) if the file has the
    wrong shape or a bad cell."""
    rows, columns = size
    try:
        lines = read_csv_file(path, skip_blank_lines=False)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        problems.add("output files", f"{where} can't be read ({error}).")
        return None
    wrong_width = any(len(values) != columns for _, values in lines)
    if len(lines) != rows or wrong_width:
        widths = sorted({len(values) for _, values in lines})
        if widths:
            seats = " or ".join(str(width) for width in widths)
        else:
            seats = "0"
        problems.add("room shape", f"{where}: {len(lines)} rows of {seats} seats; this room "
                                   f"has {rows} rows of {columns} seats.")
        return None

    grid = []
    good = True
    for row_number, (_, values) in enumerate(lines, start=1):
        grid_row = []
        for column_number, text in enumerate(values, start=1):
            if text == "":
                grid_row.append(None)
                continue
            parts = text.split(":")
            if len(parts) != 2 or "" in parts:
                problems.add("room cell", f"{where} row {row_number}, column {column_number}: "
                                          f"'{text}' should be PAPER:STUDENT or empty.")
                good = False
                grid_row.append(None)
                continue
            paper_id, student_id = parts
            grid_row.append((paper_id, student_id))
        grid.append(grid_row)
    if not good:
        return None
    someone_sits = False
    for grid_row in grid:
        for cell in grid_row:
            if cell is not None:
                someone_sits = True
    if not someone_sits:
        problems.add("output files",
                     f"{where}: no student sits here; only rooms in use get a file.")
        return None
    return grid


# stage 2: rows on their own

def slot_text(slot):
    day, session = slot
    return f"{day} {session}"


def check_date_sheet(schedule_rows, data, problems):
    """Each paper has exactly one row, with its own course codes, on an exam
    day. Returns ({paper_id: slot}, {paper_id: schedule row}, papers left out
    of the later checks)."""
    rows_of_paper = {}
    for row in schedule_rows:
        rows_of_paper.setdefault(row["paper_id"], []).append(row)

    slot_of = {}
    row_of = {}
    skipped = set()
    for paper_id, rows in sorted(rows_of_paper.items()):
        if paper_id not in data["codes_of_paper"]:
            for row in rows:
                problems.add("date sheet", f"schedule.csv row {row['_row']}: {paper_id} is "
                                           f"not a paper in the input.")
            skipped.add(paper_id)
            continue
        if len(rows) > 1:
            numbers = ", ".join(str(row["_row"]) for row in rows)
            problems.add("date sheet", f"{paper_id} has {len(rows)} rows in schedule.csv "
                                       f"(rows {numbers}); a paper is written in exactly "
                                       f"one slot.")
            skipped.add(paper_id)
            continue
        row = rows[0]
        slot_of[paper_id] = (row["_day"], row["session"])
        row_of[paper_id] = row
        check_date_sheet_row(row, data, problems)

    for paper_id in sorted(data["codes_of_paper"]):
        if paper_id not in rows_of_paper:
            problems.add("date sheet",
                         f"{paper_id} is not in schedule.csv; every paper gets one slot.")
            skipped.add(paper_id)
    return slot_of, row_of, skipped


def check_date_sheet_row(row, data, problems):
    """One paper's row: its course codes, its number of students, its day."""
    paper_id = row["paper_id"]
    where = f"schedule.csv row {row['_row']}"
    codes = sorted(code for code in row["course_codes"].split(";") if code)
    expected = sorted(data["codes_of_paper"][paper_id])
    if codes != expected:
        problems.add("same paper", f"{where}: {paper_id} lists "
                                   f"{';'.join(codes) or 'no codes'}, but its course "
                                   f"codes are {';'.join(expected)}.")
    students = len(data["students_of_paper"][paper_id])
    if row["students"] != str(students):
        problems.add("date sheet", f"{where}: {paper_id} says {row['students']} students; "
                                   f"{students} are registered.")

    day = row["_day"]
    weekday = WEEKDAY_NAMES[day.weekday()]
    reason = None
    if day < data["start"] or day > data["end"]:
        reason = f"outside {data['start']} to {data['end']}"
    elif weekday not in data["weekdays"]:
        reason = f"a {weekday}, not an exam weekday"
    elif day in data["holidays"]:
        reason = "a holiday"
    if reason:
        problems.add("exam days", f"{where}: {paper_id} is on {day}, {reason}.")


def check_seats_alone(room_files, data, slot_of, row_of, skipped, problems):
    """Each seat on its own: the student exists and is registered for the
    paper, and the paper is written in that slot. Returns (good Seats,
    students of bad seats, papers seated outside their slot, (paper_id, slot)
    pairs with a seat holding a wrong student)."""
    good_seats = []
    bad_students = set()
    wrong_student = set()
    # (paper_id, slot) -> [Seat, ...] of a paper seated outside its slot
    wrong_slot = {}
    for seat in seats_of(room_files):
        paper_id = seat.paper_id
        student_id = seat.student_id
        # a paper whose date sheet row is wrong is reported there
        if paper_id in skipped:
            bad_students.add(student_id)
        elif paper_id not in data["students_of_paper"]:
            problems.add("registration", f"{seat.where}: {paper_id} is not a paper in the input.")
            bad_students.add(student_id)
        elif student_id not in data["section_of"]:
            problems.add("registration",
                         f"{seat.where}: {student_id} is not a student in the input.")
            wrong_student.add((paper_id, seat.slot))
            bad_students.add(student_id)
        elif student_id not in data["students_of_paper"][paper_id]:
            problems.add("registration", f"{seat.where}: {student_id} sits for {paper_id}, "
                                         f"but is not registered for it.")
            wrong_student.add((paper_id, seat.slot))
            bad_students.add(student_id)
        elif seat.slot != slot_of[paper_id]:
            wrong_slot.setdefault((paper_id, seat.slot), []).append(seat)
            bad_students.add(student_id)
        else:
            good_seats.append(seat)

    report_wrong_slots(wrong_slot, slot_of, row_of, problems)
    wrong_slot_papers = {paper_id for paper_id, _ in wrong_slot}
    return good_seats, bad_students, wrong_slot_papers, wrong_student


def seats_of(room_files):
    """A Seat for every filled seat of the room files, room by room, front
    row first."""
    seats = []
    for room_file in room_files:
        for row_number, grid_row in enumerate(room_file.grid, start=1):
            for column_number, cell in enumerate(grid_row, start=1):
                if cell is None:
                    continue
                paper_id, student_id = cell
                seats.append(Seat(f"{room_file.where} row {row_number}, column {column_number}",
                                  room_file.slot, room_file.room_id, row_number, column_number,
                                  paper_id, student_id))
    return seats


def report_wrong_slots(wrong_slot, slot_of, row_of, problems):
    """One problem per paper and slot where a paper sits outside its own slot.
    wrong_slot: {(paper_id, slot): [Seat, ...]}."""
    for (paper_id, slot), seats in sorted(wrong_slot.items()):
        planned = (f"schedule.csv row {row_of[paper_id]['_row']} has it on "
                   f"{slot_text(slot_of[paper_id])}")
        if len(seats) == 1:
            problems.add("paper in its slot", f"{seats[0].where}: {paper_id} sits here on "
                                              f"{slot_text(slot)}, but {planned}.")
        else:
            rooms = ", ".join(sorted({seat.room_id for seat in seats}))
            problems.add("paper in its slot", f"{paper_id} has {len(seats)} seats on "
                                              f"{slot_text(slot)} ({rooms}), but {planned}.")


def check_duty_rows_alone(duty_rows, data, room_files, problems):
    """Each duty row on its own: a known teacher, in a room in use in that
    slot. Returns (good rows, (slot, room_id) of rooms named in a bad row)."""
    room_slots = {(room_file.slot, room_file.room_id) for room_file in room_files}
    good_rows = []
    rooms_of_bad_rows = set()
    for row in duty_rows:
        slot = (row["_day"], row["session"])
        where = f"duties.csv row {row['_row']}"
        if row["teacher_id"] not in data["rank_of"]:
            problems.add("known teacher",
                         f"{where}: {row['teacher_id']} is not in teachers.csv.")
            rooms_of_bad_rows.add((slot, row["room_id"]))
        elif (slot, row["room_id"]) not in room_slots:
            problems.add("duty in a used room",
                         f"{where}: {row['teacher_id']} has a duty in {row['room_id']} on "
                         f"{slot_text(slot)}, but no student sits there then.")
        else:
            good_rows.append(row)
    return good_rows, rooms_of_bad_rows


# stage 3: the rules over many rows

def check_gap(data, slot_of, doubtful, problems):
    """A student's papers are at least min_gap_days apart. One problem per
    pair of papers, not per student. Papers in `doubtful` are left out: their
    real date is not known."""
    papers_of_student = {}
    for paper_id, students in data["students_of_paper"].items():
        if paper_id in slot_of and paper_id not in doubtful:
            for student_id in students:
                papers_of_student.setdefault(student_id, set()).add(paper_id)

    # (paper_a, paper_b) -> students who write both, too close together
    shared = {}
    for student_id, papers in papers_of_student.items():
        papers = sorted(papers)
        for index, paper_a in enumerate(papers):
            for paper_b in papers[index + 1:]:
                day_a, _ = slot_of[paper_a]
                day_b, _ = slot_of[paper_b]
                if abs((day_a - day_b).days) < data["gap"]:
                    shared.setdefault((paper_a, paper_b), []).append(student_id)

    for (paper_a, paper_b), students in sorted(shared.items()):
        day_a, _ = slot_of[paper_a]
        day_b, _ = slot_of[paper_b]
        days = abs((day_a - day_b).days)
        problems.add("gap", f"{paper_a} ({day_a}) and {paper_b} ({day_b}) are {days} day(s) "
                            f"apart and share {len(students)} student(s), e.g. "
                            f"{min(students)}; min_gap_days is {data['gap']}.")


def check_rooms(room_files, good_seats, problems):
    """Per room: at most two papers, one paper per seat column, the column
    rule. Only the first rule a room breaks is reported. Returns the
    (slot, paper_id) pairs of the rooms reported, so later rules leave them
    out."""
    seats_of_room = {}
    for seat in good_seats:
        seats_of_room.setdefault((seat.slot, seat.room_id), []).append(seat)

    reported = set()
    for room_file in room_files:
        seats = seats_of_room.get((room_file.slot, room_file.room_id), [])
        papers = sorted({seat.paper_id for seat in seats})
        columns = len(room_file.grid[0])
        papers_in_column = [set() for _ in range(columns)]
        for seat in seats:
            papers_in_column[seat.column - 1].add(seat.paper_id)
        where = room_file.where

        shared_column = None
        for number, column_papers in enumerate(papers_in_column, start=1):
            if len(column_papers) > 1 and shared_column is None:
                shared_column = number
        side_by_side = []
        for index in range(columns - 1):
            for paper_id in sorted(papers_in_column[index] & papers_in_column[index + 1]):
                side_by_side.append((index, paper_id))

        broken = True
        if len(papers) > 2:
            problems.add("two papers at most", f"{where}: {len(papers)} papers "
                                               f"({', '.join(papers)}); a room holds at most two.")
        elif shared_column is not None:
            sharing = ", ".join(sorted(papers_in_column[shared_column - 1]))
            problems.add("one paper per column",
                         f"{where}, column {shared_column}: {sharing} share one seat column.")
        elif side_by_side:
            index, paper_id = side_by_side[0]
            problems.add("column rule", column_rule_text(where, index, paper_id, seats))
        else:
            broken = False
        if broken:
            for paper_id in papers:
                reported.add((room_file.slot, paper_id))
    return reported


def column_rule_text(where, index, paper_id, seats):
    """The problem with both columns' seats of the paper, so the stray seat is
    easy to spot; which side is wrong can't be known."""
    lines = [f"{where}, columns {index + 1} and {index + 2}: {paper_id} sits in both, "
             f"side by side."]
    for column in (index + 1, index + 2):
        seats_here = [seat for seat in seats if seat.column == column and seat.paper_id == paper_id]
        seats_here.sort(key=front_row_first)
        rows_text = ", ".join(str(seat.row) for seat in seats_here)
        students = ", ".join(seat.student_id for seat in seats_here)
        word = "row" if len(seats_here) == 1 else "rows"
        lines.append(f"    column {column}: {word} {rows_text} ({students})")
    return "\n".join(lines)


def check_seated_once(data, slot_of, good_seats, bad_students, wrong_student, reported,
                      problems):
    """Every registered student of a paper has exactly one seat in its slot.
    One problem per paper; the papers reported are added to `reported`.

    If a seat of the paper also holds a wrong student (Rule: registration),
    both problems stay: the checker can't tell which missing student belonged
    in that seat, and guessing could hide a student who really has no seat."""
    seats_of_paper = {}
    for seat in good_seats:
        seats_of_paper.setdefault(seat.paper_id, []).append(seat)

    for paper_id, slot in sorted(slot_of.items()):
        where_of = {}
        for seat in seats_of_paper.get(paper_id, []):
            where_of.setdefault(seat.student_id, []).append(seat.where)
        twice = sorted(student for student, places in where_of.items() if len(places) > 1)
        missing = sorted(data["students_of_paper"][paper_id] - set(where_of) - bad_students)
        if not twice and not missing:
            continue

        parts = []
        for student in twice:
            parts.append(f"{student} has {len(where_of[student])} seats "
                         f"({'; '.join(where_of[student])})")
        if missing:
            shown = ", ".join(missing[:5])
            more = f" and {len(missing) - 5} more" if len(missing) > 5 else ""
            parts.append(f"no seat for {len(missing)} registered student(s): {shown}{more}")
        text = f"{paper_id} on {slot_text(slot)}: {'; '.join(parts)}."
        if missing and (paper_id, slot) in wrong_student:
            text += ("\n    Shown as well as Rule: registration: a seat of this paper holds "
                     "a wrong student, and the checker can't tell which missing student "
                     "belonged there. Guessing could hide a student who really has no seat.")
        problems.add("seated once", text)
        reported.add((slot, paper_id))


def check_roll_order(data, slot_of, good_seats, reported, problems):
    """Each paper's students sit in roll order (student_id): front to back
    down each column, columns left to right, rooms in rooms.csv order. One
    problem per paper."""
    room_index = {room_id: index for index, room_id in enumerate(data["room_order"])}
    seats_of_paper = {}
    for seat in good_seats:
        seats_of_paper.setdefault(seat.paper_id, []).append(seat)

    # rooms in rooms.csv order, then down each column, columns left to right
    def in_seating_order(seat):
        return (room_index[seat.room_id], seat.column, seat.row)

    for paper_id, slot in sorted(slot_of.items()):
        if (slot, paper_id) in reported:
            continue
        seats = sorted(seats_of_paper.get(paper_id, []), key=in_seating_order)
        for before, after in zip(seats, seats[1:]):
            if after.student_id <= before.student_id:
                problems.add("roll order", f"{paper_id} on {slot_text(slot)}: "
                                           f"{after.student_id} ({after.where}) comes after "
                                           f"{before.student_id} ({before.where}).")
                break


def check_duties(duty_rows, rooms_of_bad_rows, room_files, data, slot_of, doubtful,
                 good_seats, problems):
    """One duty per slot, teachers per room, never with their own students, a
    duty for each paper they teach. A teacher in a slot is reported at most
    once. Papers in `doubtful` get no own-paper check: their real slot is not
    known."""
    # (slot, teacher_id) -> [row, ...]
    rows_of_teacher = {}
    for row in duty_rows:
        slot = (row["_day"], row["session"])
        rows_of_teacher.setdefault((slot, row["teacher_id"]), []).append(row)

    reported = check_one_duty_per_slot(rows_of_teacher, problems)
    check_teachers_per_room(duty_rows, rooms_of_bad_rows, room_files, data, problems)
    contents = room_contents(good_seats, data)
    check_own_students(rows_of_teacher, contents, data, reported, problems)
    check_own_paper_duty(rows_of_teacher, contents, room_files, good_seats, data, slot_of,
                         doubtful, reported, problems)


def check_one_duty_per_slot(rows_of_teacher, problems):
    """Returns the (slot, teacher_id) pairs reported."""
    reported = set()
    for (slot, teacher_id), rows in sorted(rows_of_teacher.items()):
        if len(rows) > 1:
            rooms = ", ".join(row["room_id"] for row in rows)
            numbers = ", ".join(str(row["_row"]) for row in rows)
            problems.add("one duty per slot",
                         f"{teacher_id} has {len(rows)} duties on {slot_text(slot)} "
                         f"({rooms}; duties.csv rows {numbers}).")
            reported.add((slot, teacher_id))
    return reported


def check_teachers_per_room(duty_rows, rooms_of_bad_rows, room_files, data, problems):
    teachers_of_room = {}
    for row in duty_rows:
        slot = (row["_day"], row["session"])
        teachers_of_room.setdefault((slot, row["room_id"]), set()).add(row["teacher_id"])

    for room_file in room_files:
        key = (room_file.slot, room_file.room_id)
        # a room named in a bad duty row is reported there
        if key in rooms_of_bad_rows:
            continue
        teachers = sorted(teachers_of_room.get(key, set()))
        if len(teachers) != data["per_room"]:
            names = ", ".join(teachers) or "none"
            problems.add("teachers per room",
                         f"{room_file.room_id} on {slot_text(room_file.slot)} has "
                         f"{len(teachers)} teacher(s) ({names}); it needs {data['per_room']}.")


def room_contents(good_seats, data):
    """{(slot, room_id): set of (paper_id, section_id) seated there}."""
    contents = {}
    for seat in good_seats:
        pair = (seat.paper_id, data["section_of"][seat.student_id])
        contents.setdefault((seat.slot, seat.room_id), set()).add(pair)
    return contents


def check_own_students(rows_of_teacher, contents, data, reported, problems):
    for (slot, teacher_id), rows in sorted(rows_of_teacher.items()):
        if (slot, teacher_id) in reported:
            continue
        teaches = data["teaches"].get(teacher_id, set())
        for row in rows:
            own = sorted(contents.get((slot, row["room_id"]), set()) & teaches)
            if own:
                paper_id, section_id = own[0]
                problems.add("own students",
                             f"duties.csv row {row['_row']}: {teacher_id} is in "
                             f"{row['room_id']} on {slot_text(slot)}, with their own "
                             f"students ({paper_id}, {section_id}).")
                reported.add((slot, teacher_id))
                break


def check_own_paper_duty(rows_of_teacher, contents, room_files, good_seats, data, slot_of,
                         doubtful, reported, problems):
    """The rule the planner uses: a teacher (not a PhD scholar) needs a duty
    in their paper's slot, in a room with their paper and none of their own
    students; if no room is like that, in a room without their paper and with
    none of their own students."""
    rooms_in_slot = {}
    for room_file in room_files:
        rooms_in_slot.setdefault(room_file.slot, []).append(room_file.room_id)
    papers_in_room = {}
    for seat in good_seats:
        papers_in_room.setdefault((seat.slot, seat.room_id), set()).add(seat.paper_id)

    for teacher_id in sorted(data["teaches"]):
        if data["rank_of"].get(teacher_id) == PHD:
            continue
        teaches = data["teaches"][teacher_id]
        for paper_id in sorted({paper for paper, _ in teaches}):
            if paper_id not in slot_of or paper_id in doubtful:
                continue
            slot = slot_of[paper_id]
            if (slot, teacher_id) in reported:
                continue
            allowed = own_paper_rooms(paper_id, teaches, slot, rooms_in_slot, contents,
                                      papers_in_room)
            duty_rooms = {row["room_id"] for row in rows_of_teacher.get((slot, teacher_id), [])}
            if duty_rooms & set(allowed):
                continue
            report_own_paper_duty(teacher_id, paper_id, slot, allowed, duty_rooms, problems)
            reported.add((slot, teacher_id))


def own_paper_rooms(paper_id, teaches, slot, rooms_in_slot, contents, papers_in_room):
    """The rooms a teacher may take for paper_id in its slot: those with the
    paper and none of their own students, or if there are none, those
    without the paper and with none of their own students."""
    with_paper = []
    without_paper = []
    for room_id in rooms_in_slot.get(slot, []):
        if contents.get((slot, room_id), set()) & teaches:
            continue
        if paper_id in papers_in_room.get((slot, room_id), set()):
            with_paper.append(room_id)
        else:
            without_paper.append(room_id)
    if with_paper:
        return with_paper
    return without_paper


def report_own_paper_duty(teacher_id, paper_id, slot, allowed, duty_rooms, problems):
    if not allowed:
        problems.add("own paper duty", f"{teacher_id} teaches {paper_id} ({slot_text(slot)}), "
                                       f"but every room in that slot holds their own students.")
        return
    if duty_rooms:
        now = f"they are in {', '.join(sorted(duty_rooms))}"
    else:
        now = "they have no duty then"
    problems.add("own paper duty", f"{teacher_id} teaches {paper_id} ({slot_text(slot)}) and "
                                   f"needs a duty in one of {', '.join(allowed)}; {now}.")


if __name__ == "__main__":
    sys.exit(main())
