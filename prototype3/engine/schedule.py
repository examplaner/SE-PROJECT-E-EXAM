"""Step 4: give every paper a date and a session (model spec section 8).

Papers go biggest first (most students, ties by paper ID). A paper goes into a
session at least min_gap_days away from every paper it shares a student with,
and only if the session still works with it (check_session()): step 5 can
really seat it, there are teachers enough for its rooms, and every teacher of
its papers has a room.

Which session: three ways are tried in this order, and the first that places
every paper makes the plan:
  a. the session where the paper adds the fewest rooms; on a tie, the session
     with fewer students, then the earlier day;
  b. the fewest rooms; on a tie, the earlier day, then fewer students;
  c. the earliest day it fits, the emptier session of that day.
Fewer rooms mean fewer duties, and fewer students mean less crowd at one time.

A paper that would leave a teacher with no room while it is alone may wait in
an empty session for another paper. A later paper that fixes a waiting session
goes there first. A session still waiting at the end means no plan.

No student ever has two papers on one day, so the session never causes a clash.
"""

import datetime
from dataclasses import dataclass

import duties
import seat
from errors import NoPlan
from exam import Paper

FEWEST_ROOMS_FEWER_STUDENTS = "fewest rooms, then the session with fewer students"
FEWEST_ROOMS_EARLIER_DAY = "fewest rooms, then the earlier day"
EARLIEST_DAY = "earliest day"
WAYS = [FEWEST_ROOMS_FEWER_STUDENTS, FEWEST_ROOMS_EARLIER_DAY, EARLIEST_DAY]

# what each way means, in words for the people who read the plan
BASIS_OF_WAY = {
    FEWEST_ROOMS_FEWER_STUDENTS:
        "biggest papers first; each paper goes into the session where it "
        "adds the fewest rooms (on a tie, the session with fewer students).",
    FEWEST_ROOMS_EARLIER_DAY:
        "biggest papers first; each paper goes into the session where it "
        "adds the fewest rooms (on a tie, the earlier day).",
    EARLIEST_DAY:
        "biggest papers first; each paper goes on the earliest day it fits "
        "(the emptier session of that day).",
}


@dataclass
class Placement:
    date: datetime.date
    session: str
    paper: Paper


def make_schedule(exam):
    """Returns (placements, the way that made them, the ways that failed
    before it). Placements are sorted by date, session and paper ID. Raises
    NoPlan with a short reason if no way places every paper."""
    if not exam.days:
        raise NoPlan("No plan possible.\n"
                     "Rule: exam days\n"
                     "settings.yaml gives no exam day: check the window, "
                     "exam_weekdays and holidays.")
    check_before_scheduling(exam)
    clashes = build_clashes(exam.papers)

    # session checks already done: the same papers give the same answer
    # in every way, so the ways share them
    checked = {}
    failed = []
    for way in WAYS:
        try:
            placements = place_papers(way, exam, clashes, checked)
        except NoPlan:
            if way == WAYS[-1]:
                raise
            failed.append(way)
            continue
        return placements, way, failed


def basis_line(way, failed):
    """One line saying on what basis the timetable was made, and which ways
    were tried first."""
    line = "Timetable basis: " + BASIS_OF_WAY[way]
    if failed:
        names = " and ".join(f'"{name}"' for name in failed)
        line += f" Tried first, but could not place every paper: {names}."
    return line


def biggest_first(paper):
    """Sort key: the most students first, ties by paper ID."""
    return (-len(paper.students), paper.paper_id)


def size_then_id(paper):
    """Sort key: the number of students, then the paper ID."""
    return (len(paper.students), paper.paper_id)


def by_paper_id(paper):
    """Sort key: the paper ID."""
    return paper.paper_id


def build_clashes(papers):
    """{paper_id: set of the paper_ids that share a student with it}."""
    papers_of_student = {}
    for paper in papers.values():
        for student in paper.students:
            papers_of_student.setdefault(student, set()).add(paper.paper_id)

    clashes = {paper_id: set() for paper_id in papers}
    for student_papers in papers_of_student.values():
        for paper_id in student_papers:
            clashes[paper_id] |= student_papers - {paper_id}
    return clashes


def seat_limit(rooms):
    """The most students of one session with one paper per room."""
    return sum(room.alone_seats() for room in rooms)


def most_papers_in_window(days, gap):
    """The most papers one student can write on these days with at least
    `gap` days between two: take the first day, then the first day at least
    `gap` days later, and so on."""
    count = 0
    last = None
    for day in days:
        if last is None or (day - last).days >= gap:
            count += 1
            last = day
    return count


def check_before_scheduling(exam):
    """Cheap checks that show straight away that no plan can exist (model
    spec section 12). Raises NoPlan."""
    check_gap_window(exam)
    check_biggest_paper(exam)


def check_gap_window(exam):
    """No student writes more papers than the window holds with the gap."""
    papers_of = {}
    for paper in exam.papers.values():
        for student in paper.students:
            papers_of.setdefault(student, []).append(paper.paper_id)
    days = exam.days
    most = most_papers_in_window(days, exam.gap)
    too_many = []
    for student, paper_ids in papers_of.items():
        if len(paper_ids) > most:
            too_many.append(student)
    too_many.sort()
    if too_many:
        first = too_many[0]
        names = ", ".join(sorted(papers_of[first]))
        raise NoPlan("No plan possible.\n"
                     "Rule: gap\n"
                     f"Student: {first} writes {len(papers_of[first])} papers ({names}).\n"
                     f"The window has {len(days)} exam days ({days[0]} to {days[-1]}). "
                     f"With at least {exam.gap} days between two papers of a student, "
                     f"at most {most} papers fit.\n"
                     f"Students with more papers than that: {len(too_many)}.")


def check_biggest_paper(exam):
    """The biggest paper fits in one session. A paper alone can't use
    neighbouring columns, so one paper per room is the most seats it can
    ever get."""
    if not exam.papers:
        return
    # on a tie in size, the paper with the highest ID
    biggest = max(exam.papers.values(), key=size_then_id)
    limit = seat_limit(exam.rooms)
    if len(biggest.students) <= limit:
        return
    if len(exam.rooms) == 1:
        rooms_give = "The only room gives"
    else:
        rooms_give = f"All {len(exam.rooms)} rooms together give"
    raise NoPlan("No plan possible.\n"
                 "Rule: seats\n"
                 f"Paper: {biggest.paper_id} ({len(biggest.students)} students)\n"
                 f"{rooms_give} {limit} seats to one paper (every other seat column), so no "
                 f"session can seat it.")


def check_session(papers, exam):
    """Can one session hold these papers? Returns (problem, rooms). problem is
    None if yes, otherwise the first check that fails: "seats", "teachers" or
    "duty room". rooms is how many rooms step 5 opens for them (0 when it
    can't seat them)."""
    if not papers:
        return None, 0
    students = sum(len(paper.students) for paper in papers)
    if students > seat_limit(exam.rooms):
        return "seats", 0
    try:
        plans = seat.seat_slot(papers, exam)
    except NoPlan:
        return "seats", 0
    if len(plans) * exam.per_room > len(exam.rank_of):
        return "teachers", len(plans)
    if duties.teachers_without_room(papers, plans, exam):
        return "duty room", len(plans)
    return None, len(plans)


class Timetable:
    """The sessions while one way places the papers."""

    def __init__(self, exam, checked):
        self.exam = exam
        self.checked = checked
        self.papers_in = {}
        self.students_in = {}
        for day in exam.days:
            for session in exam.sessions:
                self.papers_in[(day, session)] = []
                self.students_in[(day, session)] = 0
        self.date_of = {}

    def place(self, paper, slot):
        self.papers_in[slot].append(paper)
        self.students_in[slot] += len(paper.students)
        day, _ = slot
        self.date_of[paper.paper_id] = day

    def emptiest(self, slots):
        """The slot with the fewest students; on a tie the first one."""
        best = slots[0]
        for slot in slots[1:]:
            if self.students_in[slot] < self.students_in[best]:
                best = slot
        return best

    def check(self, slot, extra):
        """check_session() for the slot's papers plus the list `extra`."""
        papers = self.papers_in[slot] + extra
        key = tuple(sorted(paper.paper_id for paper in papers))
        if key not in self.checked:
            self.checked[key] = check_session(papers, self.exam)
        return self.checked[key]

    def problem(self, slot, extra):
        problem, _ = self.check(slot, extra)
        return problem

    def rooms_added(self, slot, paper):
        _, rooms_with_paper = self.check(slot, [paper])
        _, rooms_now = self.check(slot, [])
        return rooms_with_paper - rooms_now

    def is_waiting(self, slot):
        """A session waiting for another paper: a teacher of its papers has
        no room."""
        return bool(self.papers_in[slot]) and self.problem(slot, []) == "duty room"

    def can_wait_in(self, slot, paper):
        """The paper may wait in an empty session if its only problem is a
        teacher who needs another paper's room."""
        return not self.papers_in[slot] and self.problem(slot, [paper]) == "duty room"

    def free_days(self, paper, clashes):
        """The exam days at least min_gap_days from every placed paper that
        shares a student with this one."""
        days = []
        for day in self.exam.days:
            too_close = False
            for other in clashes[paper.paper_id]:
                if other in self.date_of and abs((day - self.date_of[other]).days) < self.exam.gap:
                    too_close = True
            if not too_close:
                days.append(day)
        return days


def place_papers(way, exam, clashes, checked):
    """Place every paper, choosing each paper's session in one way. Returns
    the sorted Placements, or raises NoPlan."""
    timetable = Timetable(exam, checked)
    order = sorted(exam.papers.values(), key=biggest_first)
    for paper in order:
        free_days = timetable.free_days(paper, clashes)
        slot = waiting_slot_fixed_by(paper, free_days, timetable)
        if slot is None:
            slot = choose_slot(way, paper, free_days, timetable)
        if slot is None:
            raise no_day_fits(paper, free_days, timetable)
        timetable.place(paper, slot)

    for slot, papers in timetable.papers_in.items():
        if timetable.is_waiting(slot):
            raise still_waiting(slot, papers, exam)

    placements = []
    for (day, session), papers in timetable.papers_in.items():
        for paper in sorted(papers, key=by_paper_id):
            placements.append(Placement(day, session, paper))
    return placements


def waiting_slot_fixed_by(paper, free_days, timetable):
    """The first session waiting for another paper that this paper fixes."""
    for day in free_days:
        for session in timetable.exam.sessions:
            slot = (day, session)
            if timetable.is_waiting(slot) and timetable.problem(slot, [paper]) is None:
                return slot
    return None


def choose_slot(way, paper, free_days, timetable):
    """The session the paper goes into, by `way`, or None if none can take it."""
    sessions = timetable.exam.sessions
    if way == EARLIEST_DAY:
        for day in free_days:
            day_slots = [(day, session) for session in sessions]
            fitting = [slot for slot in day_slots if timetable.problem(slot, [paper]) is None]
            if fitting:
                return timetable.emptiest(fitting)
            for slot in day_slots:
                if timetable.can_wait_in(slot, paper):
                    return slot
        return None

    slots = []
    for day in free_days:
        for session in sessions:
            slots.append((day, session))
    fitting = [slot for slot in slots if timetable.problem(slot, [paper]) is None]
    if fitting:
        # the lowest rank; on a tie the first slot
        best = None
        best_rank = None
        for slot in fitting:
            rank = slot_rank(way, slot, paper, timetable)
            if best_rank is None or rank < best_rank:
                best = slot
                best_rank = rank
        return best
    for slot in slots:
        if timetable.can_wait_in(slot, paper):
            return slot
    return None


def slot_rank(way, slot, paper, timetable):
    """How good a session is for the paper in the fewest-rooms ways: the
    lowest rank wins."""
    day, session = slot
    rooms = timetable.rooms_added(slot, paper)
    students = timetable.students_in[slot]
    session_number = timetable.exam.sessions.index(session)
    if way == FEWEST_ROOMS_FEWER_STUDENTS:
        return (rooms, students, day, session_number)
    return (rooms, day, students, session_number)


def no_day_fits(paper, free_days, timetable):
    """The NoPlan when a paper fits in no session, with every reason counted."""
    exam = timetable.exam
    blocked = {"seats": 0, "teachers": 0, "duty room": 0}
    for day in free_days:
        for session in exam.sessions:
            blocked[timetable.problem((day, session), [paper])] += 1
    open_days = len(free_days)
    return NoPlan(
        "No plan possible.\n"
        "Rule: paper placement\n"
        f"Paper: {paper.paper_id} ({len(paper.students)} students)\n"
        f"No exam day can take it. Every reason, of {len(exam.days)} exam days:\n"
        f"- gap rule: {len(exam.days) - open_days} days are less than {exam.gap} days "
        f"from a paper that shares students with it\n"
        f"- on the other {open_days} days ({open_days * len(exam.sessions)} sessions):\n"
        f"  - seats: {blocked['seats']} sessions have no seats left for it (at most "
        f"{seat_limit(exam.rooms)} seats, one paper per room, two in a room only when "
        f"rooms run out)\n"
        f"  - teachers: {blocked['teachers']} sessions would need more teachers than the "
        f"{len(exam.rank_of)} there are ({exam.per_room} per room)\n"
        f"  - duty room: {blocked['duty room']} sessions would leave a teacher of a paper "
        f"with no room to invigilate")


def still_waiting(slot, papers, exam):
    """The NoPlan when a session is still waiting for another paper at the end."""
    plans = seat.seat_slot(papers, exam)
    missing = duties.teachers_without_room(papers, plans, exam)
    names = ", ".join(f"{teacher} ({paper_id})" for teacher, paper_id in missing)
    paper_ids = ", ".join(paper.paper_id for paper in papers)
    day, session = slot
    return NoPlan("No plan possible.\n"
                  "Rule: duty room\n"
                  f"Slot: {day} {session}\n"
                  f"Papers: {paper_ids}. No other paper could join this slot, so these "
                  f"teachers have no room they may invigilate for their paper: {names}.")


def fullest_session(placements, exam):
    """(date, session, students, seat limit) of the session with the most
    students, so a run shows how close the plan is to the seat limit."""
    students_in = {}
    for placement in placements:
        slot = (placement.date, placement.session)
        students_in[slot] = students_in.get(slot, 0) + len(placement.paper.students)
    # the most students; on a tie the first slot
    fullest = None
    for slot, students in students_in.items():
        if fullest is None or students > students_in[fullest]:
            fullest = slot
    day, session = fullest
    return day, session, students_in[fullest], seat_limit(exam.rooms)
