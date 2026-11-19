"""Step 5: give every student a seat (model spec section 9).

Each slot is seated the first way that works:
  1. Best mix. One paper per room, in every other seat column, with the mix
     of room sizes that needs the fewest rooms (room_mix.py). Each paper's
     rooms are filled in rooms.csv order, its students in roll order. If a
     teacher who teaches every section of a paper would have no room without
     their own students, that paper is split by section and the mix is tried
     again.
  2. Rooms in order. If the best mix still leaves a teacher with no room, or
     can't seat the slot: one paper per room, rooms taken in rooms.csv order.
  3. Mixing, only if the rooms run out: each paper fills alone the rooms it
     fills completely, and the leftovers share the rooms still free.
After 1 or 2, two papers' leftovers (their part-empty last rooms) share one
room wherever that frees a room and every teacher still has a room.

A paper's sections each start a new room when that costs the paper no extra
room, so each section's teacher can have a room without their own students.

A room is drawn as the invigilator at the front sees it: row 1 is the front
row, column 1 is on the left.
"""

from dataclasses import dataclass

import duties
import room_mix
from errors import NoPlan


@dataclass
class RoomPlan:
    room_id: str
    # the IDs of the papers in this room: one or two
    papers: list
    # grid[row][column] is (paper_id, student_id), or None for an empty seat
    grid: list


def seat_slot(papers, exam):
    """Seat one slot. papers: the Papers written in it. Returns RoomPlans of
    the rooms in use, in rooms.csv order. Raises NoPlan if the rooms run out
    even with mixing."""
    plans, short = seat_best_for_teachers(papers, exam)
    if plans is not None and not short:
        return join_leftovers(plans, papers, exam)
    plans_in_order = seat_in_room_order(papers, exam)
    if plans_in_order is not None:
        return join_leftovers(plans_in_order, papers, exam)
    # the best mix seats everyone but leaves a teacher with no room: step 4
    # reports that teacher
    if plans is not None:
        return plans

    plans, unseated = seat_with_mixing(papers, exam.rooms)
    if unseated:
        total = 0
        for paper in papers:
            total += len(paper.students)
        missing = 0
        names = []
        for paper_id, students in sorted(unseated.items()):
            missing += len(students)
            names.append(f"{paper_id} ({len(students)})")
        if len(exam.rooms) == 1:
            rooms_used = "The only room is in use, with two papers in it"
        else:
            rooms_used = f"All {len(exam.rooms)} rooms are in use, with two papers in a room"
        raise NoPlan("No plan possible.\n"
                     "Rule: seats\n"
                     f"{rooms_used} where needed, but {missing} of {total} students still "
                     f"have no seat: {', '.join(names)}.")
    return plans


def make_seating(placements, exam):
    """Returns {(date, session): [RoomPlan, ...]}, slots in schedule order."""
    papers_of_slot = {}
    for placement in placements:
        slot = (placement.date, placement.session)
        papers_of_slot.setdefault(slot, []).append(placement.paper)

    seating = {}
    for (day, session), papers in papers_of_slot.items():
        # step 4 already asked seat_slot() about every session it booked, so
        # this is a backup that names the slot
        try:
            seating[(day, session)] = seat_slot(papers, exam)
        except NoPlan as reason:
            first_line, rest = str(reason).split("\n", 1)
            raise NoPlan(f"{first_line}\nSlot: {day} {session}\n{rest}")
    return seating


def papers_short(papers, plans, exam):
    """IDs of the papers with a teacher who has no room they may take."""
    short = set()
    for _, paper_id in duties.teachers_without_room(papers, plans, exam):
        short.add(paper_id)
    return short


def fill_columns(grid, columns, paper_id, students):
    """Seat students down each column, front to back. Seated students are
    taken off the front of the list."""
    for column in columns:
        for row in grid:
            if not students:
                return
            row[column] = (paper_id, students.pop(0))


def seat_room(room, groups):
    """Fill one room. groups: one or two (paper_id, students); the first gets
    the odd columns, the second the even columns."""
    grid = []
    for _ in range(room.rows):
        grid.append([None] * room.columns)

    first_id, first_students = groups[0]
    fill_columns(grid, room.odd_columns(), first_id, first_students)
    papers = [first_id]
    if len(groups) == 2:
        second_id, second_students = groups[1]
        fill_columns(grid, room.even_columns(), second_id, second_students)
        papers.append(second_id)
    return RoomPlan(room.room_id, papers, grid)


def paper_queues(papers):
    """(paper_id, students in roll order) for each paper, biggest first, ties
    by paper ID."""
    queues = []
    for paper in papers:
        queues.append((paper.paper_id, sorted(paper.students)))
    queues.sort(key=lambda queue: (-len(queue[1]), queue[0]))
    return queues


def section_runs(students, section_of):
    """Split students in roll order into runs of one section each."""
    runs = []
    for student in students:
        if runs:
            last_student = runs[-1][-1]
            if section_of[last_student] == section_of[student]:
                runs[-1].append(student)
                continue
        runs.append([student])
    return runs


def positions(rooms):
    """{room_id: place in rooms.csv}."""
    position = {}
    for index, room in enumerate(rooms):
        position[room.room_id] = index
    return position


def seat_best_for_teachers(papers, exam):
    """Way 1. Returns (plans, IDs of papers whose teacher still has no room),
    or (None, None) if the best mix can't seat the slot."""
    must_split = set()
    while True:
        plans = seat_best(papers, exam, must_split)
        if plans is None:
            return None, None
        short = papers_short(papers, plans, exam)
        # done, or splitting more papers can't help
        if not short or short.issubset(must_split):
            return plans, short
        must_split |= short


def seat_best(papers, exam, must_split):
    """One paper per room with the best mix of room sizes. Papers in
    must_split are split by section. Returns RoomPlans in rooms.csv order, or
    None if the mix can't seat the slot."""
    sizes, available = room_mix.room_sizes(exam.rooms)
    position = positions(exam.rooms)
    queues = paper_queues(papers)
    split = papers_to_split(queues, exam.section_of, sizes, available, must_split)

    while True:
        groups = []
        for paper_id, students in queues:
            if paper_id in split:
                for run in section_runs(students, exam.section_of):
                    groups.append((paper_id, run))
            else:
                groups.append((paper_id, list(students)))

        group_sizes = [len(students) for _, students in groups]
        chosen = room_mix.best_combination(group_sizes, sizes, available)
        if chosen is None:
            return None
        rooms_of_group = hand_out_rooms(chosen, exam.rooms, sizes, position)

        # a split paper whose sections' rooms are not in rooms.csv order would
        # break roll order: seat it straight on and search again
        broken = set()
        for paper_id in split:
            room_lists = []
            for (group_paper, _), rooms in zip(groups, rooms_of_group):
                if group_paper == paper_id:
                    room_lists.append(rooms)
            if not keeps_roll_order(room_lists, position):
                broken.add(paper_id)
        if not broken:
            break
        split -= broken

    plans = []
    for (paper_id, students), rooms in zip(groups, rooms_of_group):
        # seat_room() takes the seated students off the list, so each room
        # starts where the last one stopped
        for room in rooms:
            plans.append(seat_room(room, [(paper_id, students)]))
    plans.sort(key=lambda plan: position[plan.room_id])
    return plans


def papers_to_split(queues, section_of, sizes, available, must_split):
    """Papers whose sections each start a new room: when that needs no more
    rooms than seating the paper straight on, or when it is in must_split."""
    split = set()
    for paper_id, students in queues:
        runs = section_runs(students, section_of)
        if len(runs) < 2:
            continue
        straight = room_mix.fewest_rooms(len(students), sizes, available)
        by_section = []
        for run in runs:
            by_section.append(room_mix.fewest_rooms(len(run), sizes, available))
        if straight is None or None in by_section:
            continue
        if paper_id in must_split or sum(by_section) <= straight:
            split.add(paper_id)
    return split


def hand_out_rooms(chosen, rooms, sizes, position):
    """Real rooms for each group's option: the first free rooms of each size,
    in rooms.csv order. Returns one list of rooms per group."""
    free = {}
    for size in sizes:
        free[size] = [room for room in rooms if room.alone_seats() == size]

    rooms_of_group = []
    for option in chosen:
        taken = []
        for count, size in zip(option, sizes):
            taken += free[size][:count]
            free[size] = free[size][count:]
        taken.sort(key=lambda room: position[room.room_id])
        rooms_of_group.append(taken)
    return rooms_of_group


def keeps_roll_order(room_lists, position):
    """True if each list's rooms all come before the next list's rooms in
    rooms.csv order."""
    for before, after in zip(room_lists, room_lists[1:]):
        last_before = max(position[room.room_id] for room in before)
        first_after = min(position[room.room_id] for room in after)
        if last_before > first_after:
            return False
    return True


def rooms_needed(groups, rooms, first_index):
    """How many rooms, from rooms[first_index] on, the groups need if each
    group starts in a new room, alone. None if the rooms run out."""
    index = first_index
    for group in groups:
        left = len(group)
        while left > 0:
            if index == len(rooms):
                return None
            left -= rooms[index].alone_seats()
            index += 1
    return index - first_index


def seat_in_room_order(papers, exam):
    """Way 2: one paper per room, rooms taken in rooms.csv order. Returns
    RoomPlans, or None if the rooms run out."""
    rooms = exam.rooms
    plans = []
    room_index = 0
    for paper_id, students in paper_queues(papers):
        straight = rooms_needed([students], rooms, room_index)
        if straight is None:
            return None
        runs = section_runs(students, exam.section_of)
        if rooms_needed(runs, rooms, room_index) == straight:
            groups = runs
        else:
            groups = [students]
        # seat_room() takes the seated students off the group, so each
        # group ends when its list is empty
        for group in groups:
            while group:
                plans.append(seat_room(rooms[room_index], [(paper_id, group)]))
                room_index += 1
    return plans


def seat_with_mixing(papers, rooms):
    """Way 3. Returns (RoomPlans, {paper_id: students still without a seat})."""
    plans = []
    leftovers = []
    room_index = 0

    # each paper first fills, alone, the rooms it fills completely;
    # seat_room() takes the seated students off its list
    for paper_id, students in paper_queues(papers):
        while room_index < len(rooms) and len(students) >= rooms[room_index].alone_seats():
            plans.append(seat_room(rooms[room_index], [(paper_id, students)]))
            room_index += 1
        if students:
            leftovers.append((paper_id, students))

    # the leftovers go into the rooms still free, biggest in the odd columns;
    # a second one joins in the even columns only if otherwise the leftovers
    # would not fit in the free rooms
    for index in range(room_index, len(rooms)):
        leftovers = still_unseated(leftovers)
        if not leftovers:
            break
        leftovers.sort(key=lambda leftover: (-len(leftover[1]), leftover[0]))
        room = rooms[index]
        free_rooms_after = len(rooms) - index - 1
        groups = [leftovers[0]]
        if len(leftovers) - 1 > free_rooms_after:
            groups.append(pick_partner(leftovers[1:], room))
        plans.append(seat_room(room, groups))

    unseated = {}
    for paper_id, students in still_unseated(leftovers):
        unseated[paper_id] = students
    return plans, unseated


def still_unseated(leftovers):
    """The (paper_id, students) leftovers that still have students."""
    left = []
    for paper_id, students in leftovers:
        if students:
            left.append((paper_id, students))
    return left


def pick_partner(leftovers, room):
    """The biggest leftover that fits completely in the room's even columns;
    if none fits, the biggest. leftovers is sorted biggest first."""
    for paper_id, students in leftovers:
        if len(students) <= room.partner_seats():
            return paper_id, students
    return leftovers[0]


def join_leftovers(plans, papers, exam):
    """Put two papers' leftovers in one room wherever that frees a room.
    plans: one-paper RoomPlans of a slot. Returns RoomPlans in rooms.csv order.

    For example, A has 13 students left in an M room and B has 8 in another:
    one M room holds both (A in columns 1, 3, 5 and B in 2, 4, 6), and one
    room and its invigilators are saved."""
    room_of = {}
    for room in exam.rooms:
        room_of[room.room_id] = room
    position = positions(exam.rooms)
    plans = sorted(plans, key=lambda plan: position[plan.room_id])
    if papers_short(papers, plans, exam):
        return plans

    # pairs whose join would leave a teacher with no room
    refused = set()
    while True:
        leftovers = leftover_rooms(plans, room_of)
        choice = best_join(plans, leftovers, room_of, position, refused)
        if choice is None:
            return plans
        first_id, second_id, shared = choice
        joined = seat_room(room_of[shared.room_id], [
            (first_id, students_of(leftovers[first_id], first_id)),
            (second_id, students_of(leftovers[second_id], second_id))])
        trial = []
        for plan in plans:
            if plan is not leftovers[first_id] and plan is not leftovers[second_id]:
                trial.append(plan)
        trial.append(joined)
        trial.sort(key=lambda plan: position[plan.room_id])
        if papers_short(papers, trial, exam):
            refused.add((first_id, second_id))
        else:
            plans = trial


def students_of(plan, paper_id):
    """A paper's students in a room, in the order they were seated: down each
    column, columns left to right."""
    students = []
    for column in range(len(plan.grid[0])):
        for row in plan.grid:
            cell = row[column]
            if cell and cell[0] == paper_id:
                students.append(cell[1])
    return students


def leftover_rooms(plans, room_of):
    """{paper_id: RoomPlan} for each paper whose last room (in rooms.csv
    order) holds only that paper and is part empty."""
    last_room = {}
    for plan in plans:
        for paper_id in plan.papers:
            last_room[paper_id] = plan

    leftovers = {}
    for paper_id, plan in last_room.items():
        if len(plan.papers) != 1:
            continue
        seated = len(students_of(plan, paper_id))
        if 0 < seated < room_of[plan.room_id].alone_seats():
            leftovers[paper_id] = plan
    return leftovers


def best_join(plans, leftovers, room_of, position, refused):
    """The best pair of leftovers to share one room, as (first_id, second_id,
    shared RoomPlan), or None. The first paper is the bigger leftover (odd
    columns); the shared room is one of the two leftover rooms. Best is the
    fewest empty seats, then the room higher in rooms.csv, then the paper IDs.
    Pairs in `refused` are skipped."""
    size = {}
    for paper_id, plan in leftovers.items():
        size[paper_id] = len(students_of(plan, paper_id))
    order = sorted(leftovers, key=lambda paper_id: (-size[paper_id], paper_id))

    best_rank = None
    best_choice = None
    for index, first_id in enumerate(order):
        for second_id in order[index + 1:]:
            if (first_id, second_id) in refused:
                continue
            for shared in (leftovers[first_id], leftovers[second_id]):
                room = room_of[shared.room_id]
                if size[first_id] > room.alone_seats() or size[second_id] > room.partner_seats():
                    continue
                if shared is leftovers[first_id]:
                    moving_id = second_id
                else:
                    moving_id = first_id
                if has_room_after(plans, moving_id, leftovers[moving_id], shared, position):
                    continue
                empty = (room.alone_seats() + room.partner_seats()
                         - size[first_id] - size[second_id])
                rank = (empty, position[shared.room_id], first_id, second_id)
                if best_rank is None or rank < best_rank:
                    best_rank = rank
                    best_choice = (first_id, second_id, shared)
    return best_choice


def has_room_after(plans, paper_id, its_leftover, shared, position):
    """True if the paper has a room, other than its leftover room, after the
    shared room in rooms.csv. Moving its leftover there would break roll
    order."""
    for plan in plans:
        if (paper_id in plan.papers and plan is not its_leftover
                and position[plan.room_id] > position[shared.room_id]):
            return True
    return False


def two_paper_rooms(seating):
    """How many rooms of the whole seating hold two papers."""
    count = 0
    for plans in seating.values():
        for plan in plans:
            if len(plan.papers) == 2:
                count += 1
    return count


def basis_line(seating):
    """One line saying on what basis the seating was made."""
    rooms = 0
    for plans in seating.values():
        rooms += len(plans)
    two = two_paper_rooms(seating)
    line = ("Seating basis: one paper per room, with the mix of room sizes "
            "that needs the fewest rooms; ")
    if two == 0:
        return line + f"all {rooms} rooms hold one paper."
    one = rooms - two
    one_text = "1 room holds" if one == 1 else f"{one} rooms hold"
    two_text = "1 holds" if two == 1 else f"{two} hold"
    return line + (f"{one_text} one paper and {two_text} two (two papers' "
                   f"leftovers joined, or mixed where the rooms ran out).")


def cell_text(cell):
    """A room CSV cell: 'PAPER:STUDENT', or blank for an empty seat."""
    if cell is None:
        return ""
    paper_id, student_id = cell
    return f"{paper_id}:{student_id}"
