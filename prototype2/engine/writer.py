"""Write a plan folder (model spec section 11), or why.txt when no plan is
possible (section 12)."""

import csv
import datetime
import shutil
from pathlib import Path

import seat

SCHEDULE_COLUMNS = ["date", "session", "paper_id", "course_codes", "students"]
DUTY_COLUMNS = ["date", "session", "room_id", "teacher_id"]
# the page that explains the words of the plan; every plan folder gets a
# copy, so whoever gets the folder can read it
TERMS_FILE = Path(__file__).resolve().parent / "docs" / "terms.md"
TERMS_LINE = "If a word in these lines is not clear, read terms.md in the plan folder."


def new_plan_folder(output_root):
    """A new folder named by the time of the run, YYYY-MM-DD_HH-MM-SS. A
    second run in the same second gets _2, _3, ..."""
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder = Path(output_root) / stamp
    number = 2
    while folder.exists():
        folder = Path(output_root) / f"{stamp}_{number}"
        number += 1
    folder.mkdir(parents=True)
    return folder


def write_why(reason, folder):
    """why.txt is the only file of a run with no plan, so there is never a
    half plan. Returns its path."""
    path = folder / "why.txt"
    path.write_text(reason + "\n", encoding="utf-8")
    return path


def write_schedule(placements, path):
    """schedule.csv, one row per paper. A paper's course codes are joined
    with ';' so the cell needs no quotes."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(SCHEDULE_COLUMNS)
        for placement in placements:
            paper = placement.paper
            writer.writerow([placement.date.isoformat(), placement.session, paper.paper_id,
                             ";".join(paper.course_codes), len(paper.students)])


def write_seating(seating, folder):
    """daywise_seating_plans/<date>/<session>/<room_id>.csv for every room in
    use. No header: each CSV row is a row of seats, front first. Returns the
    number of files."""
    count = 0
    for (day, session), plans in seating.items():
        slot_folder = folder / "daywise_seating_plans" / day.isoformat() / session
        slot_folder.mkdir(parents=True, exist_ok=True)
        for plan in plans:
            with open(slot_folder / f"{plan.room_id}.csv", "w", newline="",
                      encoding="utf-8") as file:
                writer = csv.writer(file)
                for row in plan.grid:
                    writer.writerow([seat.cell_text(cell) for cell in row])
            count += 1
    return count


def write_duties(rows, path):
    """duties.csv, one row per teacher per room per slot."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(DUTY_COLUMNS)
        for day, session, room_id, teacher_id in rows:
            writer.writerow([day.isoformat(), session, room_id, teacher_id])


def write_basis(lines, folder):
    """basis.txt (on what basis the plan was made) and a copy of terms.md.
    The terms line is added when terms.md is copied. Returns the lines
    written, which main.py also prints."""
    # a copy, so the caller's list doesn't get the terms line
    lines = list(lines)
    if TERMS_FILE.is_file():
        shutil.copyfile(TERMS_FILE, folder / "terms.md")
        lines.append(TERMS_LINE)
    (folder / "basis.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines
