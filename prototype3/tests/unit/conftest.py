"""What the unit tests share: where the datasets are, small made-up exams, and
the inputs as the app picks them.

Run from prototype3/:

    python -m pytest tests/unit
"""

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

PROTOTYPE = Path(__file__).resolve().parents[2]
# the app's modules sit in prototype3/, the planner's in prototype3/engine/
sys.path.insert(0, str(PROTOTYPE))
sys.path.insert(0, str(PROTOTYPE / "engine"))

import duties  # noqa: E402
import loader  # noqa: E402
import main  # noqa: E402
import schedule  # noqa: E402
import seat  # noqa: E402
from exam import Exam, Paper, Room, build_exam  # noqa: E402

# 16 students, 3 rooms, 9 teachers, one week: small enough to check by hand
SMALL_DATASET = PROTOTYPE / "data" / "tiny"
# 1,600 students, 36 rooms, 85 teachers, three weeks
REALISTIC_DATASET = PROTOTYPE / "data" / "main"
IMPOSSIBLE_DATASETS = PROTOTYPE / "data" / "impossible"


@pytest.fixture
def small_copy(tmp_path):
    """A copy of the small dataset that a test may break."""
    folder = tmp_path / "input"
    shutil.copytree(SMALL_DATASET, folder)
    return folder


def made_up_paper(paper_id, count):
    """A paper with students A01, A02, ... named after the paper."""
    students = set()
    for number in range(1, count + 1):
        students.add(f"{paper_id}{number:02d}")
    return Paper(paper_id, [paper_id], students)


def s_room(room_id):
    """A small room: 6 rows of 3 seats, 12 seats for one paper alone."""
    return Room(room_id, 6, 3)


def m_room(room_id):
    """A medium room: 7 rows of 6 seats, 21 seats for one paper alone."""
    return Room(room_id, 7, 6)


def made_up_exam(papers, rooms, section_of=None, teaching=None, rank_of=None,
                 days=None, sessions=None, per_room=2):
    """An Exam for unit tests. By default each paper's students are one
    section named after the paper, nobody teaches anything, and there are 99
    teachers, so only the seats can be a problem."""
    if section_of is None:
        section_of = {}
        for paper in papers:
            for student in paper.students:
                section_of[student] = paper.paper_id
    if rank_of is None:
        rank_of = {}
        for number in range(1, 100):
            rank_of[f"T{number:03d}"] = "ASST"
    papers_by_id = {paper.paper_id: paper for paper in papers}
    return Exam(papers_by_id, rooms, section_of, teaching or {}, rank_of, days or [],
                sessions or ["morning", "evening"], 2, per_room)


def exam_of(dataset):
    return build_exam(loader.load(loader.input_paths(dataset)))


@dataclass
class Planned:
    exam: Exam
    placements: list
    # the way of choosing sessions that made the schedule, and those that failed
    way: str
    failed: list
    seating: dict
    duty_rows: list


# dataset -> its Planned; each dataset is planned once for all the tests
PLANS = {}


def plan_of(dataset):
    """The whole plan of a dataset, made the way main.py makes it."""
    if dataset not in PLANS:
        exam = exam_of(dataset)
        placements, way, failed = schedule.make_schedule(exam)
        seating = seat.make_seating(placements, exam)
        duty_rows = duties.make_duties(seating, exam)
        PLANS[dataset] = Planned(exam, placements, way, failed, seating, duty_rows)
    return PLANS[dataset]


def replace_once(path, old, new):
    """Change a file a test breaks on purpose. The text must be in it
    exactly once, so the change is the one the test means."""
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"test setup: {old!r} in {path}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def run_main(input_dir, output_dir, capsys):
    """Run main.py; returns (exit code, printed text, the one new folder, or
    None when there is none)."""
    code = main.main([str(input_dir), "--output", str(output_dir)])
    printed = capsys.readouterr().out
    folders = list(output_dir.iterdir()) if output_dir.exists() else []
    assert len(folders) <= 1
    folder = folders[0] if folders else None
    return code, printed, folder


def inputs_of(folder):
    """The nine inputs of a dataset folder, as the app would have them
    picked: {input key: path}."""
    return loader.input_paths(folder)
