"""Step 6, the duties (model spec section 10), and the duty rule steps 4 and 5
ask."""

import datetime
from functools import lru_cache

import pytest

import duties
import loader
import schedule
import seat
from conftest import REALISTIC_DATASET, SMALL_DATASET
from errors import NoPlan
from exam import PHD, Exam, build_exam

DAY_1 = datetime.date(2026, 11, 2)
DAY_2 = datetime.date(2026, 11, 3)

# paper P is written by sections A_I (student a1) and A_II (a2), paper Q by
# B_I (b1) and B_II (b2); each room here has one seat
SECTION_OF = {"a1": "A_I", "a2": "A_II", "b1": "B_I", "b2": "B_II"}


def room(room_id, paper_id, student_id):
    return seat.RoomPlan(room_id, [paper_id], [[(paper_id, student_id)]])


R1 = room("R1", "P", "a1")
R2 = room("R2", "P", "a2")
R3 = room("R3", "Q", "b1")
R4 = room("R4", "Q", "b2")


def hand_exam(rank_of, teaching, per_room):
    """A made-up Exam with the rooms above. teaching: {teacher: {(paper,
    section)}}."""
    return Exam({}, [], SECTION_OF, teaching, rank_of, [], ["morning", "evening"], 2, per_room)


def rooms_for(teaches, plans):
    contents = duties.room_contents(plans, SECTION_OF)
    return duties.rooms_for_paper("P", teaches, plans, contents)


def teachers_of_rooms(rows):
    """{room_id: [teacher_id, ...]} for duty rows of one slot."""
    found = {}
    for _, _, room_id, teacher_id in rows:
        found.setdefault(room_id, []).append(teacher_id)
    return found


def test_first_choice_is_a_room_with_the_paper_but_none_of_own_students():
    assert rooms_for({("P", "A_I")}, [R1, R2, R3]) == ["R2"]


def test_otherwise_a_room_with_a_different_paper():
    # every P room has their own students, so the room writing Q
    assert rooms_for({("P", "A_I"), ("P", "A_II")}, [R1, R2, R3]) == ["R3"]


def test_never_a_room_with_own_students_of_any_paper():
    assert rooms_for({("P", "A_I"), ("P", "A_II"), ("Q", "B_I")}, [R1, R2, R3]) == []


def test_teachers_without_room_skips_phd_scholars():
    exam = hand_exam({"T1": "ASST", "T2": "PHD"},
                     {"T1": {("P", "A_I"), ("P", "A_II")},
                      "T2": {("P", "A_I"), ("P", "A_II")}}, per_room=2)
    p_paper = schedule.Paper("P", ["P"], {"a1", "a2"})
    assert duties.teachers_without_room([p_paper], [R1, R2], exam) == [("T1", "P")]


def test_own_paper_duty_comes_first():
    # T1 teaches P to A_I: only R2 counts as their P duty. Without that rule
    # T1, the lowest ID, would take R1.
    exam = hand_exam({"T1": "ASST", "T2": "ASST", "T3": "ASST"},
                     {"T1": {("P", "A_I")}}, per_room=1)
    rows = duties.make_duties({(DAY_1, "morning"): [R1, R2, R3]}, exam)
    assert teachers_of_rooms(rows) == {"R1": ["T2"], "R2": ["T1"], "R3": ["T3"]}


def test_a_chain_of_moves_finds_a_place():
    # one teacher per room. T1 takes R1 and T2 takes R2; for T3 both are
    # full. T3 takes R1, T1 moves to R2, and T2 moves to R3.
    may_sit = {"T1": {"R1", "R2"}, "T2": {"R2", "R3"}, "T3": {"R1", "R2"}}
    teachers_in = {"R1": [], "R2": [], "R3": []}
    for teacher_id in ["T1", "T2", "T3"]:
        assert duties.place_teacher(teacher_id, teachers_in, 1, may_sit, set())
    assert teachers_in == {"R1": ["T3"], "R2": ["T1"], "R3": ["T2"]}


def test_a_chain_that_fails_changes_nothing():
    may_sit = {"T1": {"R1"}, "T2": {"R1"}}
    teachers_in = {"R1": []}
    assert duties.place_teacher("T1", teachers_in, 1, may_sit, set())
    assert not duties.place_teacher("T2", teachers_in, 1, may_sit, set())
    assert teachers_in == {"R1": ["T1"]}


def test_phd_scholars_only_when_no_regular_teacher_is_free():
    exam = hand_exam({"T1": "PROF", "T2": "ASST", "T9": "PHD"}, {}, per_room=2)
    rows = duties.make_duties({(DAY_1, "morning"): [R3]}, exam)
    assert teachers_of_rooms(rows) == {"R3": ["T1", "T2"]}

    exam = hand_exam({"T1": "PROF", "T9": "PHD"}, {}, per_room=2)
    rows = duties.make_duties({(DAY_1, "morning"): [R3]}, exam)
    assert teachers_of_rooms(rows) == {"R3": ["T1", "T9"]}


def test_a_second_shift_on_one_day_comes_after_fewest_duties():
    # T1 has fewer duties but already works on 2 Nov, so T2 goes first that
    # day; on 3 Nov the counts decide
    counts = {"T1": 1, "T2": 3}
    days_worked = {"T1": {DAY_1}}
    assert duties.best_first(["T1", "T2"], DAY_1, counts, days_worked) == ["T2", "T1"]
    assert duties.best_first(["T1", "T2"], DAY_2, counts, days_worked) == ["T1", "T2"]

    exam = hand_exam({"T1": "ASST", "T2": "ASST"}, {}, per_room=1)
    rows = duties.make_duties({(DAY_1, "morning"): [R3], (DAY_1, "evening"): [R3]}, exam)
    assert [(row[1], row[3]) for row in rows] == [("morning", "T1"), ("evening", "T2")]


def test_no_plan_when_the_teachers_run_out():
    exam = hand_exam({"T1": "ASST"}, {}, per_room=2)
    with pytest.raises(NoPlan) as error:
        duties.make_duties({(DAY_1, "morning"): [R3]}, exam)
    assert "Rule: duties" in str(error.value)
    assert "Short: R3 has 1." in str(error.value)


def test_no_plan_when_the_own_paper_rooms_are_full():
    # T1 and T2 both teach all of P: their only room is R3, with one place
    both_sections = {("P", "A_I"), ("P", "A_II")}
    exam = hand_exam({"T1": "ASST", "T2": "ASST"},
                     {"T1": both_sections, "T2": both_sections}, per_room=1)
    with pytest.raises(NoPlan) as error:
        duties.make_duties({(DAY_1, "morning"): [R1, R2, R3]}, exam)
    assert "Rule: duty room" in str(error.value)
    assert "They are full of other teachers" in str(error.value)


def test_no_plan_when_two_own_papers_need_different_rooms():
    # T1 teaches P to A_I and Q to B_I, both in this slot: the P duty counts
    # only in R2, the Q duty only in R4, and a teacher has one duty per slot
    exam = hand_exam({"T1": "ASST"}, {"T1": {("P", "A_I"), ("Q", "B_I")}}, per_room=1)
    with pytest.raises(NoPlan) as error:
        duties.make_duties({(DAY_1, "morning"): [R1, R2, R3, R4]}, exam)
    assert "no one room counts as a duty for all of them" in str(error.value)


def test_one_own_paper_with_no_room_is_no_plan():
    # a backup: step 4 stops this before booking
    contents = duties.room_contents([R1], SECTION_OF)
    with pytest.raises(NoPlan) as error:
        duties.own_paper_rooms("T1", {("P", "A_I")}, [R1], contents, DAY_1, "morning")
    assert "every room in this slot has their own students" in str(error.value)


@lru_cache
def staffed(dataset):
    """(exam, seating, duty rows) of a dataset, worked out once."""
    exam = build_exam(loader.load(loader.input_paths(dataset)))
    placements, _, _ = schedule.make_schedule(exam)
    seating = seat.make_seating(placements, exam)
    return exam, seating, duties.make_duties(seating, exam)


@pytest.mark.parametrize("dataset", [SMALL_DATASET, REALISTIC_DATASET])
def test_every_duty_rule_holds_on_both_datasets(dataset):
    exam, seating, rows = staffed(dataset)
    for (day, session), plans in seating.items():
        slot_rows = [row for row in rows if row[:2] == (day, session)]
        in_room = teachers_of_rooms(slot_rows)
        teachers = [row[3] for row in slot_rows]
        # one duty per slot, and every room has its teachers
        assert len(teachers) == len(set(teachers))
        assert set(in_room) == {plan.room_id for plan in plans}
        contents = duties.room_contents(plans, exam.section_of)
        for plan in plans:
            assert len(in_room[plan.room_id]) == exam.per_room
            for teacher_id in in_room[plan.room_id]:
                assert not contents[plan.room_id] & exam.teaching.get(teacher_id, set())
        # every regular teacher of a paper here sits in a room that counts
        papers_here = {paper_id for plan in plans for paper_id in plan.papers}
        for teacher_id, teaches in exam.teaching.items():
            if exam.rank_of[teacher_id] == PHD:
                continue
            mine = [row[2] for row in slot_rows if row[3] == teacher_id]
            for paper_id in {paper for paper, _ in teaches} & papers_here:
                assert mine and mine[0] in duties.rooms_for_paper(paper_id, teaches, plans,
                                                                  contents)


def test_duties_are_spread_on_the_realistic_dataset():
    exam, _, rows = staffed(REALISTIC_DATASET)
    numbers = duties.duty_summary(rows, exam)
    assert numbers["phd_duties"] == 0
    assert numbers["most"] - numbers["fewest"] <= 1
