"""Step 5, the seating (model spec section 9)."""

from functools import lru_cache

import pytest

import loader
import room_mix
import schedule
import seat
from conftest import REALISTIC_DATASET, SMALL_DATASET, m_room, made_up_exam, made_up_paper, s_room
from errors import NoPlan
from exam import build_exam

BOTH_DATASETS = [SMALL_DATASET, REALISTIC_DATASET]


def seat_papers(papers, rooms, section_of=None, teaching=None):
    """Seat one slot of made-up papers."""
    exam = made_up_exam(papers, rooms, section_of=section_of, teaching=teaching)
    return seat.seat_slot(papers, exam)


def picture(plan):
    """A room as text, like its CSV: the student, or '.' for an empty seat."""
    lines = []
    for row in plan.grid:
        cells = []
        for cell in row:
            cells.append(cell[1] if cell else ".")
        lines.append(" ".join(cells))
    return lines


def room_ids(plans):
    return [plan.room_id for plan in plans]


def papers_of(plans):
    return [plan.papers for plan in plans]


def fill_order(plans, paper_id):
    """The paper's students as they were seated: room by room, down each
    column, columns left to right."""
    students = []
    for plan in plans:
        students += seat.students_of(plan, paper_id)
    return students


def two_sections(paper_id, count, first_section_size):
    """section_of for a made-up paper whose first students are section X and
    the rest section Y."""
    section_of = {}
    for number in range(1, count + 1):
        section_of[f"{paper_id}{number:02d}"] = "X" if number <= first_section_size else "Y"
    return section_of


# one paper per room, best mix of room sizes

def test_one_paper_alone_uses_every_other_column_in_roll_order():
    # A (21) fits M01 alone, B (12) fits S01: 2 rooms. In M01, A01-A07 go
    # down column 1, A08-A14 down column 3, A15-A21 down column 5.
    plans = seat_papers([made_up_paper("A", 21), made_up_paper("B", 12)],
                        [s_room("S01"), m_room("M01"), s_room("S02")])
    assert room_ids(plans) == ["S01", "M01"]
    assert papers_of(plans) == [["B"], ["A"]]
    assert picture(plans[0]) == ["B01 . B07", "B02 . B08", "B03 . B09",
                                 "B04 . B10", "B05 . B11", "B06 . B12"]
    assert picture(plans[1]) == ["A01 . A08 . A15 .", "A02 . A09 . A16 .",
                                 "A03 . A10 . A17 .", "A04 . A11 . A18 .",
                                 "A05 . A12 . A19 .", "A06 . A13 . A20 .",
                                 "A07 . A14 . A21 ."]


def test_45_students_get_one_m_and_two_s_rooms_with_no_empty_seat():
    # M + M + S would be 54 seats, 9 empty; M + S + S is exactly 45. The
    # chosen rooms are filled in rooms.csv order, so roll order is kept.
    rooms = [s_room("S01"), s_room("S02"), s_room("S03"), m_room("M01"), m_room("M02")]
    plans = seat_papers([made_up_paper("A", 45)], rooms)
    assert room_ids(plans) == ["S01", "S02", "M01"]
    order = fill_order(plans, "A")
    assert order == sorted(order) and len(order) == 45


def test_a_few_leftover_students_do_not_get_a_big_room():
    # 24 students: M01 21 + M02 3 is two rooms, and so is S01 + S02 with
    # no empty seat, so the S rooms win
    plans = seat_papers([made_up_paper("A", 24)],
                        [m_room("M01"), m_room("M02"), s_room("S01"), s_room("S02")])
    assert room_ids(plans) == ["S01", "S02"]


def test_fewest_rooms_come_before_fewest_empty_seats():
    # 36 students: three S rooms leave no empty seat, but two M rooms are
    # fewer rooms and so fewer teachers on duty
    rooms = [s_room("S01"), s_room("S02"), s_room("S03"), m_room("M01"), m_room("M02")]
    plans = seat_papers([made_up_paper("A", 36)], rooms)
    assert room_ids(plans) == ["M01", "M02"]


def test_papers_of_a_slot_share_its_rooms():
    # one M and two S rooms for two papers of 21: one gets M01, the other
    # S01 and S02
    plans = seat_papers([made_up_paper("A", 21), made_up_paper("B", 21)],
                        [s_room("S01"), s_room("S02"), m_room("M01")])
    assert room_ids(plans) == ["S01", "S02", "M01"]
    assert plans[0].papers == plans[1].papers != plans[2].papers


def test_room_options_never_have_a_spare_room():
    for students in range(1, 80):
        for option in room_mix.room_options(students, [21, 12], [18, 18]):
            seats = option[0] * 21 + option[1] * 12
            assert seats >= students
            if option[0]:
                assert seats - 21 < students
            if option[1]:
                assert seats - 12 < students


def test_only_rooms_in_use_are_returned():
    plans = seat_papers([made_up_paper("A", 3)], [s_room("S01"), m_room("M01")])
    assert room_ids(plans) == ["S01"]


# sections and teachers

def test_each_section_starts_a_new_room_when_it_costs_no_extra_room():
    # 8 of section X and 8 of Y: straight on is S01 12 + S02 4, by section
    # S01 8 X + S02 8 Y; both are 2 rooms, so by section
    plans = seat_papers([made_up_paper("A", 16)], [s_room("S01"), s_room("S02")],
                        section_of=two_sections("A", 16, 8))
    assert seat.students_of(plans[0], "A") == [f"A{n:02d}" for n in range(1, 9)]
    assert seat.students_of(plans[1], "A") == [f"A{n:02d}" for n in range(9, 17)]


def test_sections_stay_together_when_a_new_room_would_cost_a_room():
    # 13 of X and 11 of Y: straight on is 2 rooms, by section 3
    plans = seat_papers([made_up_paper("A", 24)],
                        [s_room("S01"), s_room("S02"), s_room("S03")],
                        section_of=two_sections("A", 24, 13))
    assert room_ids(plans) == ["S01", "S02"]


def test_a_teacher_with_no_room_makes_the_paper_split_by_section():
    # 16 students fit in M01 alone, but then T001 (section X) and T002
    # (section Y) both have their own students in the only room. Split by
    # section, X in S01 and Y in S02, each takes the other section's room.
    rooms = [s_room("S01"), s_room("S02"), m_room("M01")]
    section_of = two_sections("A", 16, 8)
    plans = seat_papers([made_up_paper("A", 16)], rooms, section_of=section_of)
    assert room_ids(plans) == ["M01"]

    teaching = {"T001": {("A", "X")}, "T002": {("A", "Y")}}
    plans = seat_papers([made_up_paper("A", 16)], rooms, section_of=section_of,
                        teaching=teaching)
    assert room_ids(plans) == ["S01", "S02"]
    assert seat.students_of(plans[0], "A") == [f"A{n:02d}" for n in range(1, 9)]


def test_rooms_in_order_are_the_backup_when_a_teacher_still_has_no_room():
    # one section, and its teacher teaches all of it, so no split helps.
    # The plan in rooms.csv order comes back, and step 4 reports the teacher.
    plans = seat_papers([made_up_paper("A", 16)],
                        [s_room("S01"), s_room("S02"), m_room("M01")],
                        teaching={"T001": {("A", "A")}})
    assert room_ids(plans) == ["S01", "S02"]


# two papers in a room

def test_leftovers_are_mixed_when_the_rooms_run_out():
    # A 13 and B 13 alone need 4 S rooms, there are 3: each fills one alone,
    # and the last students share S03, A in column 1 and B in column 2
    plans = seat_papers([made_up_paper("A", 13), made_up_paper("B", 13)],
                        [s_room("S01"), s_room("S02"), s_room("S03")])
    assert papers_of(plans) == [["A"], ["B"], ["A", "B"]]
    assert picture(plans[2]) == ["A13 B13 .", ". . .", ". . .", ". . .", ". . .", ". . ."]


def test_mixing_only_where_needed():
    # A fills S01; leftovers B 5, C 3, A 1 for two free rooms, so only one
    # room gets two papers
    papers = [made_up_paper("A", 13), made_up_paper("B", 5), made_up_paper("C", 3)]
    plans = seat_papers(papers, [s_room("S01"), s_room("S02"), s_room("S03")])
    assert papers_of(plans) == [["A"], ["B", "C"], ["A"]]


def test_a_room_never_holds_a_third_paper():
    # as above with two rooms: A's last student would be a third paper
    papers = [made_up_paper("A", 13), made_up_paper("B", 5), made_up_paper("C", 3)]
    with pytest.raises(NoPlan) as error:
        seat_papers(papers, [s_room("S01"), s_room("S02")])
    assert "Rule: seats" in str(error.value)
    assert "1 of 21 students still have no seat: A (1)" in str(error.value)


def test_a_tie_in_size_goes_by_paper_id():
    plans = seat_papers([made_up_paper("Z", 6), made_up_paper("Y", 6)], [s_room("S01")])
    assert plans[0].papers == ["Y", "Z"]


def test_two_leftovers_share_one_room():
    # A 34 = 21 + 13 left, B 29 = 21 + 8 left: 4 rooms alone. The leftovers
    # share M04, which comes after both papers' full rooms, so roll order is
    # kept: A, the bigger, in columns 1, 3, 5 and B in 2, 4, 6.
    rooms = [m_room("M01"), m_room("M02"), m_room("M03"), m_room("M04")]
    plans = seat_papers([made_up_paper("A", 34), made_up_paper("B", 29)], rooms)
    assert room_ids(plans) == ["M01", "M03", "M04"]
    assert papers_of(plans) == [["A"], ["B"], ["A", "B"]]
    assert picture(plans[2]) == ["A22 B22 A29 B29 . .", "A23 B23 A30 . . .",
                                 "A24 B24 A31 . . .", "A25 B25 A32 . . .",
                                 "A26 B26 A33 . . .", "A27 B27 A34 . . .",
                                 "A28 B28 . . . ."]


def test_the_pair_that_fills_a_room_best_is_joined_first():
    # leftovers A 20, C 19, B 5: A + C leave 3 seats empty, so they share;
    # B stays alone, and a room never gets a third paper
    papers = [made_up_paper("A", 20), made_up_paper("B", 5), made_up_paper("C", 19)]
    plans = seat_papers(papers, [m_room("M01"), m_room("M02"), m_room("M03")])
    assert papers_of(plans) == [["A", "C"], ["B"]]


def test_in_an_s_room_the_bigger_leftover_takes_the_two_odd_columns():
    plans = seat_papers([made_up_paper("A", 10), made_up_paper("B", 6)],
                        [s_room("S01"), s_room("S02")])
    assert picture(plans[0]) == ["A01 B01 A07", "A02 B02 A08", "A03 B03 A09",
                                 "A04 B04 A10", "A05 B05 .", "A06 B06 ."]


def test_full_rooms_and_a_lone_paper_are_never_joined():
    two_full = seat_papers([made_up_paper("A", 21), made_up_paper("B", 21)],
                           [m_room("M01"), m_room("M02")])
    assert papers_of(two_full) == [["A"], ["B"]]
    one_paper = seat_papers([made_up_paper("A", 30)], [m_room("M01"), m_room("M02")])
    assert papers_of(one_paper) == [["A"], ["A"]]
    assert seat.basis_line({("day", "morning"): two_full}) == (
        "Seating basis: one paper per room, with the mix of room sizes that "
        "needs the fewest rooms; all 2 rooms hold one paper.")


def test_no_join_when_a_teacher_would_have_no_room():
    # T001 teaches A's first 21 students (section A1) and all of B. Joined,
    # A's leftover and B's leftover would share M04; then every room holds
    # T001's students and T001 has no room for B. So they stay apart.
    rooms = [m_room("M01"), m_room("M02"), m_room("M03"), m_room("M04")]
    papers = [made_up_paper("A", 34), made_up_paper("B", 29)]
    section_of = {}
    for student in papers[0].students:
        section_of[student] = "A1" if student <= "A21" else "A2"
    for student in papers[1].students:
        section_of[student] = "B1"
    plans = seat_papers(papers, rooms, section_of=section_of,
                        teaching={"T001": {("A", "A1"), ("B", "B1")}})
    assert papers_of(plans) == [["A"], ["A"], ["B"], ["B"]]


def test_no_join_breaks_roll_order():
    plans = seat_papers([made_up_paper("A", 5), made_up_paper("B", 26)],
                        [s_room("S01"), s_room("S02"), m_room("M01"), m_room("M02")])
    for paper_id in ("A", "B"):
        order = fill_order(plans, paper_id)
        assert order == sorted(order)
    assert len(fill_order(plans, "A") + fill_order(plans, "B")) == 31


# the rules on both datasets

@lru_cache
def seated(dataset):
    """(placements, seating) of a dataset, worked out once."""
    exam = build_exam(loader.load(loader.input_paths(dataset)))
    placements, _, _ = schedule.make_schedule(exam)
    return placements, seat.make_seating(placements, exam)


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_every_student_gets_exactly_one_seat_per_paper(dataset):
    placements, seating = seated(dataset)
    for placement in placements:
        plans = seating[(placement.date, placement.session)]
        assert sorted(fill_order(plans, placement.paper.paper_id)) == sorted(
            placement.paper.students)


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_column_rule_two_papers_at_most_and_roll_order(dataset):
    _, seating = seated(dataset)
    for slot, plans in seating.items():
        assert len(room_ids(plans)) == len(set(room_ids(plans))), slot
        for plan in plans:
            papers_in_column = []
            for column in range(len(plan.grid[0])):
                papers = {row[column][0] for row in plan.grid if row[column]}
                assert len(papers) <= 1, (slot, plan.room_id)
                papers_in_column.append(papers)
            for left, right in zip(papers_in_column, papers_in_column[1:]):
                assert not left & right, (slot, plan.room_id)
            assert len(plan.papers) <= 2
        for paper_id in {paper_id for plan in plans for paper_id in plan.papers}:
            order = fill_order(plans, paper_id)
            assert order == sorted(order), (slot, paper_id)


@pytest.mark.parametrize("dataset", BOTH_DATASETS)
def test_a_shared_room_holds_only_the_last_students_of_two_papers(dataset):
    # where the rooms don't run out, two papers share a room only as two
    # leftovers joined: each paper is in at most one shared room, and the
    # students there are its last ones in roll order
    placements, seating = seated(dataset)
    exam = build_exam(loader.load(loader.input_paths(dataset)))
    for slot, plans in seating.items():
        papers = {p.paper.paper_id: p.paper for p in placements if (p.date, p.session) == slot}
        if seat.seat_in_room_order(list(papers.values()), exam) is None:
            continue
        shared_rooms = {}
        for plan in plans:
            if len(plan.papers) != 2:
                continue
            for paper_id in plan.papers:
                shared_rooms[paper_id] = shared_rooms.get(paper_id, 0) + 1
                here = seat.students_of(plan, paper_id)
                everyone = sorted(papers[paper_id].students)
                assert here == everyone[-len(here):], (slot, plan.room_id)
        assert all(count == 1 for count in shared_rooms.values()), slot
