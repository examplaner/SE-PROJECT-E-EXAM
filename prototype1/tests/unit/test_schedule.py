"""Step 4, the timetable (model spec section 8)."""

import datetime
from functools import lru_cache

import pytest

import duties
import loader
import schedule
import seat
from conftest import (REALISTIC_DATASET, SMALL_DATASET, m_room, made_up_exam, made_up_paper,
                      run_main, s_room)
from errors import NoPlan
from exam import build_exam

BOTH_DATASETS = [SMALL_DATASET, REALISTIC_DATASET]
DAY_1 = datetime.date(2026, 11, 2)
DAY_2 = datetime.date(2026, 11, 3)


def exam_of(dataset):
    return build_exam(loader.load(loader.input_paths(dataset)))


# remember the result, so each dataset is scheduled once for all tests
@lru_cache
def scheduled(dataset):
    """(exam, placements, the way that made them, the ways that failed)."""
    exam = exam_of(dataset)
    placements, way, failed = schedule.make_schedule(exam)
    return exam, placements, way, failed


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_every_paper_gets_exactly_one_slot(dataset):
    exam, placements, _, _ = scheduled(dataset)
    assert sorted(p.paper.paper_id for p in placements) == sorted(exam.papers)


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_gap_rule_for_every_student(dataset):
    exam, placements, _, _ = scheduled(dataset)
    dates_of = {}
    for placement in placements:
        for student in placement.paper.students:
            dates_of.setdefault(student, []).append(placement.date)
    for student, dates in dates_of.items():
        dates.sort()
        for first, second in zip(dates, dates[1:]):
            assert (second - first).days >= exam.gap, (student, first, second)


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_only_exam_days_and_the_two_sessions_are_used(dataset):
    exam, placements, _, _ = scheduled(dataset)
    for placement in placements:
        assert placement.date in exam.days
        assert placement.session in exam.sessions


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_no_session_has_more_students_than_one_paper_per_room_seats(dataset):
    exam, placements, _, _ = scheduled(dataset)
    students_in = {}
    for placement in placements:
        slot = (placement.date, placement.session)
        students_in[slot] = students_in.get(slot, 0) + len(placement.paper.students)
    assert max(students_in.values()) <= schedule.seat_limit(exam.rooms)


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_every_teacher_has_a_room_for_each_paper_they_teach(dataset):
    exam, placements, _, _ = scheduled(dataset)
    seating = seat.make_seating(placements, exam)
    for slot, plans in seating.items():
        papers = [p.paper for p in placements if (p.date, p.session) == slot]
        assert duties.teachers_without_room(papers, plans, exam) == [], slot


def test_same_input_gives_same_schedule():
    _, first, _, _ = scheduled(REALISTIC_DATASET)
    second, _, _ = schedule.make_schedule(exam_of(REALISTIC_DATASET))
    assert first == second


def test_small_schedule_worked_out_by_hand():
    # Biggest first, and a session waiting for another paper is filled first.
    # CSE2001 (16): 2 Nov morning, each section in its own room so both its
    #   teachers have a room. Everyone writes it, so 3 Nov is out.
    # CSE2002 (8): T004 teaches all of it, so alone it can't work: it waits
    #   in 4 Nov morning, and ECE2001 (8) fills that session.
    # MTH2001 (5) waits in 6 Nov morning, and PHY2002 (5) fills it.
    # BIO2001 and PHY2001 (3 each) fit in 6 Nov morning, so they go there
    #   (an empty evening alone would only be waiting).
    _, placements, way, failed = scheduled(SMALL_DATASET)
    got = {(p.paper.paper_id, p.date.day, p.session) for p in placements}
    assert got == {
        ("CSE2001", 2, "morning"),
        ("CSE2002", 4, "morning"), ("ECE2001", 4, "morning"),
        ("MTH2001", 6, "morning"), ("PHY2002", 6, "morning"),
        ("BIO2001", 6, "morning"), ("PHY2001", 6, "morning"),
    }
    assert way == schedule.FEWEST_ROOMS_FEWER_STUDENTS and failed == []
    line = schedule.basis_line(way, failed)
    assert "(on a tie, the session with fewer students)." in line
    assert "Tried first" not in line


def test_realistic_dataset_falls_back_to_the_next_way_and_says_so():
    # the first way can't place ECE2003 (the gap rule leaves it no day), so
    # the second way makes the plan and the basis line says so
    _, placements, way, failed = scheduled(REALISTIC_DATASET)
    assert len(placements) == 56
    assert way == schedule.FEWEST_ROOMS_EARLIER_DAY
    assert failed == [schedule.FEWEST_ROOMS_FEWER_STUDENTS]
    line = schedule.basis_line(way, failed)
    assert "(on a tie, the earlier day)." in line
    assert ('Tried first, but could not place every paper: '
            f'"{schedule.FEWEST_ROOMS_FEWER_STUDENTS}".') in line


def test_exam_days_skip_weekends_and_holidays():
    exam = exam_of(REALISTIC_DATASET)
    assert len(exam.days) == 14
    assert datetime.date(2026, 11, 11) not in exam.days  # holiday
    assert datetime.date(2026, 11, 7) not in exam.days   # Saturday
    assert datetime.date(2026, 11, 20) in exam.days


def test_seat_limit_is_every_other_column():
    assert s_room("S01").alone_seats() == 12
    assert m_room("M01").alone_seats() == 21
    assert schedule.seat_limit(exam_of(REALISTIC_DATASET).rooms) == 594


def test_most_papers_in_window():
    def days(*numbers):
        return [datetime.date(2026, 11, number) for number in numbers]

    # Mon 2 to Fri 6 Nov with a gap of 2: 2, 4 and 6
    assert schedule.most_papers_in_window(days(2, 3, 4, 5, 6), 2) == 3
    assert schedule.most_papers_in_window(days(2, 3, 4), 2) == 2
    # Fri 6 and Mon 9 are 3 days apart, so a gap of 3 still fits both
    assert schedule.most_papers_in_window(days(6, 9), 3) == 2


# made-up papers share no students, so only seats and rooms decide

def placed_by(way, sizes, rooms, sessions):
    """Place made-up papers on 2 and 3 Nov in one way. Returns
    {paper_id: (date, session)}."""
    papers = [made_up_paper(name, count) for name, count in sizes]
    exam = made_up_exam(papers, rooms, days=[DAY_1, DAY_2], sessions=sessions)
    clashes = schedule.build_clashes(exam.papers)
    placements = schedule.place_papers(way, exam, clashes, {})
    return {p.paper.paper_id: (p.date, p.session) for p in placements}


def test_a_paper_goes_where_it_adds_the_fewest_rooms():
    # one M room (21 for one paper) and two S rooms (12 each). A and B, 21
    # each, take 2 Nov morning and evening in the M room. C (21) on 2 Nov
    # would need both S rooms (2 more rooms); on 3 Nov it gets the M room
    # (1 more room). So C goes to 3 Nov.
    sizes = [("A", 21), ("B", 21), ("C", 21)]
    rooms = [m_room("M01"), s_room("S01"), s_room("S02")]
    for way in (schedule.FEWEST_ROOMS_FEWER_STUDENTS, schedule.FEWEST_ROOMS_EARLIER_DAY):
        assert placed_by(way, sizes, rooms, ["morning", "evening"]) == {
            "A": (DAY_1, "morning"), "B": (DAY_1, "evening"), "C": (DAY_2, "morning")}
    # the last way takes the earliest day that fits: C in the two S rooms
    assert placed_by(schedule.EARLIEST_DAY, sizes, rooms, ["morning", "evening"])["C"] == (
        DAY_1, "morning")


def test_a_tie_in_rooms_goes_to_fewer_students_or_the_earlier_day():
    # one session a day. A (21) is on 2 Nov. B (5) adds one room on either
    # day: the first way takes the emptier session, the second the earlier day
    sizes = [("A", 21), ("B", 5)]
    rooms = [m_room("M01"), s_room("S01")]
    assert placed_by(schedule.FEWEST_ROOMS_FEWER_STUDENTS, sizes, rooms,
                     ["morning"])["B"] == (DAY_2, "morning")
    assert placed_by(schedule.FEWEST_ROOMS_EARLIER_DAY, sizes, rooms,
                     ["morning"])["B"] == (DAY_1, "morning")


def test_a_session_must_really_be_seatable_not_just_counted():
    # 13 + 5 + 3 = 21 students and two S rooms give 24 seats for one paper
    # per room, so counting says yes. But A fills S01, and B, C and A's last
    # student would need S02 with three papers, so the session doesn't work.
    papers = [made_up_paper("A", 13), made_up_paper("B", 5), made_up_paper("C", 3)]
    exam = made_up_exam(papers, [s_room("S01"), s_room("S02")])
    assert schedule.check_session([], exam) == (None, 0)
    assert schedule.check_session(papers[:2], exam) == (None, 2)
    assert schedule.check_session(papers, exam) == ("seats", 0)


def test_too_few_teachers_for_the_rooms():
    papers = [made_up_paper("A", 30)]
    exam = made_up_exam(papers, [m_room("M01"), m_room("M02")],
                        rank_of={"T001": "ASST", "T002": "ASST", "T003": "ASST"})
    assert schedule.check_session(papers, exam) == ("teachers", 2)


def test_when_two_ways_fail_the_last_way_makes_the_plan(monkeypatch, tmp_path, capsys):
    real_place_papers = schedule.place_papers

    def only_the_last_way(way, *rest):
        if way != schedule.EARLIEST_DAY:
            raise NoPlan("No plan possible.")
        return real_place_papers(way, *rest)

    monkeypatch.setattr(schedule, "place_papers", only_the_last_way)
    code, printed, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    assert code == 0, printed
    assert "each paper goes on the earliest day it fits" in printed
    assert (f'Tried first, but could not place every paper: '
            f'"{schedule.FEWEST_ROOMS_FEWER_STUDENTS}" and '
            f'"{schedule.FEWEST_ROOMS_EARLIER_DAY}".') in printed
    assert "Tried first" in (folder / "basis.txt").read_text(encoding="utf-8")


def test_no_plan_only_when_the_last_way_fails_too(monkeypatch):
    def nothing_works(way, *rest):
        raise NoPlan(f"No plan possible.\nway: {way}")

    monkeypatch.setattr(schedule, "place_papers", nothing_works)
    with pytest.raises(NoPlan) as error:
        schedule.make_schedule(exam_of(SMALL_DATASET))
    # the reason is the last way's
    assert schedule.EARLIEST_DAY in str(error.value)
