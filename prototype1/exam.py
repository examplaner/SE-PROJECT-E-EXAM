"""What every planning step needs, built once from a valid input: the papers,
the rooms, who sits in which section, who teaches what, and the exam days."""

import datetime
from dataclasses import dataclass, field

import loader

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PHD = "PHD"


@dataclass
class Paper:
    paper_id: str
    # in courses.csv order
    course_codes: list
    students: set = field(default_factory=set)


@dataclass
class Room:
    room_id: str
    rows: int
    columns: int

    # columns 1, 3, 5, ... as people count them: one paper alone sits here,
    # so no two neighbouring columns hold the same paper
    def odd_columns(self):
        return list(range(0, self.columns, 2))

    # columns 2, 4, 6, ...: a second paper sits here
    def even_columns(self):
        return list(range(1, self.columns, 2))

    def alone_seats(self):
        """Seats for one paper alone: S 12, M 21."""
        return self.rows * len(self.odd_columns())

    def partner_seats(self):
        """Seats for a second paper: S 6, M 21."""
        return self.rows * len(self.even_columns())


@dataclass
class Exam:
    # paper_id -> Paper, in courses.csv order
    papers: dict
    # Rooms in rooms.csv order
    rooms: list
    # student_id -> section_id
    section_of: dict
    # teacher_id -> set of (paper_id, section_id) from teaching.csv
    teaching: dict
    # teacher_id -> rank, in teachers.csv order
    rank_of: dict
    # exam days in calendar order
    days: list
    sessions: list
    gap: int
    per_room: int


def build_exam(data):
    """data: what loader.load() gives back, checked by validate.check_data()."""
    settings = data["settings"]
    papers = build_papers(data)

    rooms = []
    for row in data["rooms"]:
        rooms.append(Room(row["room_id"], int(row["rows"]), int(row["seat_columns"])))

    section_of = {}
    for student in data["students"]:
        section_of[student["student_id"]] = student["section_id"]

    rank_of = {}
    for teacher in data["teachers"]:
        rank_of[teacher["teacher_id"]] = teacher["rank"]

    sessions = [str(name) for name in settings["sessions"]]
    return Exam(papers, rooms, section_of, build_teaching(data, papers), rank_of,
                exam_days(settings), sessions, settings["min_gap_days"],
                settings["invigilators_per_room"])


def build_papers(data):
    """Codes in one same_paper group are one paper, named by the group's first
    code. Every other code is its own paper."""
    paper_of_code = {}
    for group in data["constraints"].get("same_paper") or []:
        codes = [str(code) for code in group]
        for code in codes:
            paper_of_code[code] = codes[0]

    papers = {}
    for course in data["courses"]:
        code = course["course_code"]
        paper_id = paper_of_code.get(code, code)
        if paper_id not in papers:
            papers[paper_id] = Paper(paper_id, [])
        papers[paper_id].course_codes.append(code)

    for registration in data["registrations"]:
        code = registration["course_code"]
        paper_id = paper_of_code.get(code, code)
        papers[paper_id].students.add(registration["student_id"])
    return papers


def build_teaching(data, papers):
    """{teacher_id: set of (paper_id, section_id)}."""
    paper_of_code = {}
    for paper in papers.values():
        for code in paper.course_codes:
            paper_of_code[code] = paper.paper_id

    teaching = {}
    for row in data["teaching"]:
        pair = (paper_of_code[row["course_code"]], row["section_id"])
        teaching.setdefault(row["teacher_id"], set()).add(pair)
    return teaching


def exam_days(settings):
    """Every date that can hold exams, in calendar order."""
    start = loader.as_date(settings["start_date"])
    end = loader.as_date(settings["end_date"])
    holidays = set()
    for day in settings["holidays"] or []:
        holidays.add(loader.as_date(day))

    days = []
    day = start
    while day <= end:
        if WEEKDAY_NAMES[day.weekday()] in settings["exam_weekdays"] and day not in holidays:
            days.append(day)
        day += datetime.timedelta(days=1)
    return days
