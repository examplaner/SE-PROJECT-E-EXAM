"""What the unit tests share: where the datasets are, and small made-up exams.

Run from prototype1/:

    python -m pytest tests/unit
"""

import shutil
import sys
from pathlib import Path

import pytest

PROTOTYPE = Path(__file__).resolve().parents[2]
# the planner's modules sit in prototype1/
sys.path.insert(0, str(PROTOTYPE))

import main  # noqa: E402
from exam import Exam, Paper, Room  # noqa: E402

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


def run_main(input_dir, output_dir, capsys):
    """Run main.py; returns (exit code, printed text, the one new folder, or
    None when there is none)."""
    code = main.main([str(input_dir), "--output", str(output_dir)])
    printed = capsys.readouterr().out
    folders = list(output_dir.iterdir()) if output_dir.exists() else []
    assert len(folders) <= 1
    folder = folders[0] if folders else None
    return code, printed, folder
