"""Step 6: teachers to rooms (model spec section 10), and the duty rule that
steps 4 and 5 ask before they settle a session.

Every teacher who teaches a paper (PhD scholars are exempt) needs, in that
paper's slot, a room they may take for it:
  1. a room with their paper and none of their own students, or if there is
     none,
  2. a room without their paper and with none of their own students, so they
     are near if the question paper has a mistake.
Their own students are the sections they teach (teaching.csv), whatever paper
those students write in the room.

How the places are given, slot by slot: own-paper duties first; every other
place to a teacher with no duty in the other session that day, then the one
with the fewest duties so far, then the lower teacher ID; PhD scholars only
when nobody else can be placed. If the rooms a teacher may sit in are full, a
chain of moves is tried before saying there is no plan, so a plan is found
whenever one exists.
"""

from errors import NoPlan
from exam import PHD


def room_contents(plans, section_of):
    """{room_id: set of (paper_id, section_id) seated there}, for one slot."""
    contents = {}
    for plan in plans:
        pairs = set()
        for row in plan.grid:
            for cell in row:
                if cell is None:
                    continue
                paper_id, student_id = cell
                pairs.add((paper_id, section_of[student_id]))
        contents[plan.room_id] = pairs
    return contents


def rooms_for_paper(paper_id, teaches, plans, contents):
    """The rooms a teacher may take for paper_id: rule 1's rooms if there are
    any, otherwise rule 2's (maybe none). teaches: the teacher's set of
    (paper_id, section_id)."""
    with_paper = []
    without_paper = []
    for plan in plans:
        if contents[plan.room_id] & teaches:
            continue
        if paper_id in plan.papers:
            with_paper.append(plan.room_id)
        else:
            without_paper.append(plan.room_id)
    if with_paper:
        return with_paper
    return without_paper


def papers_taught(teaches, paper_ids):
    """The papers among paper_ids that the teacher teaches, sorted.
    teaches: the teacher's set of (paper_id, section_id)."""
    taught = set()
    for paper_id, _ in teaches:
        if paper_id in paper_ids:
            taught.add(paper_id)
    return sorted(taught)


def teachers_without_room(papers, plans, exam):
    """Check one slot: papers are the Papers written in it, plans its
    RoomPlans. Returns (teacher_id, paper_id) for every teacher, not a PhD
    scholar, who has no room for that paper. Empty means the rule holds."""
    contents = room_contents(plans, exam.section_of)
    in_slot = {paper.paper_id for paper in papers}
    missing = []
    for teacher_id in sorted(exam.teaching):
        if exam.rank_of[teacher_id] == PHD:
            continue
        teaches = exam.teaching[teacher_id]
        for paper_id in papers_taught(teaches, in_slot):
            if not rooms_for_paper(paper_id, teaches, plans, contents):
                missing.append((teacher_id, paper_id))
    return missing


def make_duties(seating, exam):
    """seating: {(date, session): [RoomPlan]} from seat.make_seating().
    Returns (date, session, room_id, teacher_id) rows: slot by slot, rooms in
    rooms.csv order, a room's teachers by ID. Raises NoPlan if a room can't
    get its teachers.

    Slots go in date order, first session first, so "fewest duties so far"
    and "a duty already that day" count the slots before."""
    regulars = []
    phds = []
    for teacher_id, rank in exam.rank_of.items():
        if rank == PHD:
            phds.append(teacher_id)
        else:
            regulars.append(teacher_id)
    regulars.sort()
    phds.sort()
    counts = {}
    for teacher_id in regulars + phds:
        counts[teacher_id] = 0
    # teacher_id -> dates with a duty
    days_worked = {}

    def in_time_order(slot):
        day, session = slot
        return (day, exam.sessions.index(session))

    rows = []
    for day, session in sorted(seating, key=in_time_order):
        teachers_in = staff_slot(day, session, seating[(day, session)], exam,
                                 regulars, phds, counts, days_worked)
        for room_id, teacher_ids in teachers_in.items():
            for teacher_id in sorted(teacher_ids):
                rows.append((day, session, room_id, teacher_id))
                counts[teacher_id] += 1
                days_worked.setdefault(teacher_id, set()).add(day)
    return rows


def staff_slot(day, session, plans, exam, regulars, phds, counts, days_worked):
    """Fill every room of one slot with exam.per_room teachers. Returns
    {room_id: [teacher_id, ...]} in rooms.csv order."""
    may_sit, own_paper = rooms_teachers_may_sit(day, session, plans, exam, regulars, phds)
    teachers_in = {}
    for plan in plans:
        teachers_in[plan.room_id] = []

    def fewest_rooms_first(teacher_id):
        return (len(own_paper[teacher_id]), teacher_id)

    # 1. own-paper duties, the teachers with the fewest rooms first
    for teacher_id in sorted(own_paper, key=fewest_rooms_first):
        if not place_teacher(teacher_id, teachers_in, exam.per_room, may_sit, set()):
            rooms = []
            for room_id in teachers_in:
                if room_id in own_paper[teacher_id]:
                    rooms.append(room_id)
            raise no_plan("duty room", day, session,
                          f"{teacher_id} needs a duty for their own paper in one of these "
                          f"rooms: {', '.join(rooms)}. They are full of other teachers who "
                          f"can't sit anywhere else.")

    # 2. every other place: regular teachers best first, PhD scholars last
    others = [teacher_id for teacher_id in regulars if teacher_id not in own_paper]
    order = best_first(others, day, counts, days_worked) + best_first(phds, day, counts, days_worked)
    for teacher_id in order:
        if all_full(teachers_in, exam.per_room):
            break
        place_teacher(teacher_id, teachers_in, exam.per_room, may_sit, set())

    if not all_full(teachers_in, exam.per_room):
        raise too_few_teachers(day, session, teachers_in, exam.per_room, regulars, phds)
    return teachers_in


def rooms_teachers_may_sit(day, session, plans, exam, regulars, phds):
    """Returns ({teacher: the rooms they may sit in this slot}, {teacher: the
    rooms that count as their own-paper duty}). A teacher with a paper here
    may sit only in those rooms; any other teacher in a room without their
    own students."""
    contents = room_contents(plans, exam.section_of)
    may_sit = {}
    own_paper = {}
    for teacher_id in regulars + phds:
        teaches = exam.teaching.get(teacher_id, set())
        rooms = None
        # PhD scholars are exempt from the own-paper duty
        if teacher_id in regulars:
            rooms = own_paper_rooms(teacher_id, teaches, plans, contents, day, session)
        if rooms is not None:
            own_paper[teacher_id] = rooms
            may_sit[teacher_id] = rooms
            continue
        may_sit[teacher_id] = set()
        for room_id, inside in contents.items():
            if not (inside & teaches):
                may_sit[teacher_id].add(room_id)
    return may_sit, own_paper


def too_few_teachers(day, session, teachers_in, per_room, regulars, phds):
    """The NoPlan when some room is still short of teachers."""
    short = []
    placed = 0
    for room_id, teacher_ids in teachers_in.items():
        placed += len(teacher_ids)
        if len(teacher_ids) < per_room:
            short.append(f"{room_id} has {len(teacher_ids)}")
    return no_plan("duties", day, session,
                   f"Every room needs {per_room} teachers. Short: {', '.join(short)}.\n"
                   f"Needs {per_room * len(teachers_in)} teachers, {placed} could be placed "
                   f"({len(regulars)} regular teachers, {len(phds)} PhD scholars; nobody "
                   f"sits with their own students or has two duties in one slot).")


def own_paper_rooms(teacher_id, teaches, plans, contents, day, session):
    """The rooms that count as the teacher's own-paper duty in this slot, or
    None if no paper they teach is written here. With two of their papers
    here, one room must count for both, because a teacher has one duty per
    slot."""
    papers_here = set()
    for plan in plans:
        papers_here.update(plan.papers)
    own_papers = papers_taught(teaches, papers_here)
    if not own_papers:
        return None

    rooms = {plan.room_id for plan in plans}
    for paper_id in own_papers:
        rooms &= set(rooms_for_paper(paper_id, teaches, plans, contents))
    if not rooms:
        # step 4 checks each paper's teachers before booking, so with one own
        # paper this is a backup; with two own papers it can really happen
        if len(own_papers) == 1:
            text = (f"{teacher_id} needs a duty for {own_papers[0]}, but every room in "
                    f"this slot has their own students.")
        else:
            text = (f"{teacher_id} teaches {', '.join(own_papers)}, all written in this "
                    f"slot, and no one room counts as a duty for all of them (a teacher "
                    f"has at most one duty per slot).")
        raise no_plan("duty room", day, session, text)
    return rooms


def place_teacher(teacher_id, teachers_in, per_room, may_sit, rooms_tried):
    """Give the teacher a place in the first room they may sit in that has a
    free place, in rooms.csv order. Returns True if it worked; on False
    nothing has changed.

    If all those rooms are full: take a teacher out of one of them, put this
    teacher in, and place the one taken out in another room they may sit in,
    the same way (a chain of moves). rooms_tried holds the rooms already used
    in this chain, so it can't go round in circles."""
    rooms = [room_id for room_id in teachers_in if room_id in may_sit[teacher_id]]
    for room_id in rooms:
        if len(teachers_in[room_id]) < per_room:
            teachers_in[room_id].append(teacher_id)
            return True

    for room_id in rooms:
        if room_id in rooms_tried:
            continue
        rooms_tried.add(room_id)
        for other in list(teachers_in[room_id]):
            teachers_in[room_id].remove(other)
            teachers_in[room_id].append(teacher_id)
            if place_teacher(other, teachers_in, per_room, may_sit, rooms_tried):
                return True
            # undo: put the other teacher back
            teachers_in[room_id].remove(teacher_id)
            teachers_in[room_id].append(other)
    return False


def all_full(teachers_in, per_room):
    for teacher_ids in teachers_in.values():
        if len(teacher_ids) < per_room:
            return False
    return True


def best_first(teacher_ids, day, counts, days_worked):
    """Teachers in the order they are picked: no duty yet that day first,
    then the fewest duties so far, then the teacher ID."""
    def order(teacher_id):
        # False sorts before True, so teachers with no duty that day come first
        worked_today = day in days_worked.get(teacher_id, set())
        return (worked_today, counts[teacher_id], teacher_id)
    return sorted(teacher_ids, key=order)


def no_plan(rule, day, session, text):
    return NoPlan(f"No plan possible.\nRule: {rule}\nSlot: {day} {session}\n{text}")


def duty_summary(rows, exam):
    """The numbers main.py prints: fewest and most duties of a regular
    teacher, duties of PhD scholars, and teacher-days with both shifts."""
    counts = {}
    for teacher_id in exam.rank_of:
        counts[teacher_id] = 0
    shifts = {}
    for day, _, _, teacher_id in rows:
        counts[teacher_id] += 1
        shifts[(teacher_id, day)] = shifts.get((teacher_id, day), 0) + 1

    regular_counts = []
    phd_duties = 0
    for teacher_id, count in counts.items():
        if exam.rank_of[teacher_id] == PHD:
            phd_duties += count
        else:
            regular_counts.append(count)
    double_days = 0
    for count in shifts.values():
        if count > 1:
            double_days += 1
    return {
        "fewest": min(regular_counts, default=0),
        "most": max(regular_counts, default=0),
        "phd_duties": phd_duties,
        "double_days": double_days,
    }
