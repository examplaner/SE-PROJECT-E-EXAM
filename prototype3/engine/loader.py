"""Read an input folder into plain Python data. Checking it is validate.py's job.

load() gives back one dict:

    data["sections"], data["courses"], data["registrations"],
    data["rooms"], data["teachers"], data["teaching"]
                          the rows of each CSV file
    data["students"]      one row per line of every roster file in sections/,
                          with "section_id" and "_file" added
    data["roster_files"]  section IDs that have a roster file
    data["settings"]      settings.yaml as a dict
    data["constraints"]   constraints.yaml as a dict

A row is a dict of column -> text, plus "_row": its line number in the file,
counting the header as row 1, as a spreadsheet shows it.
"""

import csv
import datetime
from pathlib import Path

import yaml

# file key -> the header the file must have (data_design_spec.md section 2)
CSV_COLUMNS = {
    "sections": ["section_id", "cohort_id", "program", "year"],
    "courses": ["course_code", "title", "cohort_id", "kind"],
    "registrations": ["student_id", "course_code"],
    "rooms": ["room_id", "type", "rows", "seat_columns"],
    "teachers": ["teacher_id", "rank"],
    "teaching": ["teacher_id", "course_code", "section_id"],
}
ROSTER_COLUMNS = ["student_id"]


def input_paths(input_dir):
    """Where each input lives inside an input folder. "students" is the folder
    of roster files, one per section."""
    folder = Path(input_dir)
    paths = {}
    for key in CSV_COLUMNS:
        paths[key] = folder / f"{key}.csv"
    paths["students"] = folder / "sections"
    paths["settings"] = folder / "settings.yaml"
    paths["constraints"] = folder / "constraints.yaml"
    return paths


def roster_paths(students_folder):
    """Every roster file, sorted by name so the order never changes."""
    return sorted(Path(students_folder).glob("*.csv"))


def read_csv_lines(path):
    """Returns (header, rows), rows as (line number, values). Values are
    stripped, blank lines skipped, and Excel's byte-order mark ignored."""
    header = []
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        for values in reader:
            values = [value.strip() for value in values]
            if not any(values):
                continue
            if not header:
                header = values
            else:
                rows.append((reader.line_num, values))
    return header, rows


def read_table(path):
    header, rows = read_csv_lines(path)
    return [dict(zip(header, values), _row=number) for number, values in rows]


def read_yaml(path):
    """An empty file gives an empty dict."""
    with open(path, encoding="utf-8-sig") as file:
        content = yaml.safe_load(file)
    if content is None:
        return {}
    return content


def as_date(value):
    """A YAML date (2026-11-02) or 'YYYY-MM-DD' text as a date, else None."""
    # a date with a time is not what settings.yaml wants; datetime is a
    # kind of date in Python, so it is ruled out first
    if isinstance(value, datetime.datetime):
        return None
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def load(paths):
    """Read every input. `paths` is what input_paths() gives back."""
    data = {}
    for key in CSV_COLUMNS:
        data[key] = read_table(paths[key])

    data["students"] = []
    data["roster_files"] = []
    folder_name = Path(paths["students"]).name
    for path in roster_paths(paths["students"]):
        data["roster_files"].append(path.stem)
        for row in read_table(path):
            row["section_id"] = path.stem
            row["_file"] = f"{folder_name}/{path.name}"
            data["students"].append(row)

    data["settings"] = read_yaml(paths["settings"])
    data["constraints"] = read_yaml(paths["constraints"])
    return data
