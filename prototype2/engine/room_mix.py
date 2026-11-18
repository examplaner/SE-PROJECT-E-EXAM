"""The best mix of room sizes for the papers of one slot (model spec section 9).

A paper alone uses every other seat column, so an S room holds 12 and an M
room 21. Before anyone is seated, the mixes of room sizes for all papers of
the slot together are tried, and the one with the fewest rooms wins, then the
fewest empty seats. For example 45 students get 1 M and 2 S rooms (45 seats,
none empty), not 2 M and 1 S (54 seats). Fewest rooms first, because every
room needs its invigilators, while an empty seat costs nothing.
"""

import itertools

# past this many partial mixes the search stops, and seat.py falls back to
# taking rooms in rooms.csv order
MAX_STATES = 200_000


def room_sizes(rooms):
    """The different one-paper sizes, biggest first, and how many rooms have
    each size: ([21, 12], [18, 18]) for data/main."""
    count_of = {}
    for room in rooms:
        size = room.alone_seats()
        count_of[size] = count_of.get(size, 0) + 1
    sizes = sorted(count_of, reverse=True)
    counts = [count_of[size] for size in sizes]
    return sizes, counts


def room_options(students, sizes, available):
    """Every mix of rooms that seats `students` people of one paper with no
    spare room, as a tuple of room counts, one per size: (1, 2) is 1 M and
    2 S. At most available[i] rooms of size sizes[i]. In order (0, ...),
    (1, ...), ..., which decides ties later on."""
    # every count of each size but the last; the last size then takes
    # the students left over, rounded up to whole rooms
    ranges = []
    for count in available[:-1]:
        ranges.append(range(count + 1))
    last_size = sizes[-1]

    options = []
    for counts in itertools.product(*ranges):
        seats = 0
        for count, size in zip(counts, sizes):
            seats += count * size
        left = max(0, students - seats)
        last = (left + last_size - 1) // last_size
        if last > available[-1]:
            continue
        option = counts + (last,)
        total = seats + last * last_size
        # spare: one room could be taken out and everyone would still fit
        spare = False
        for count, size in zip(option, sizes):
            if count > 0 and total - size >= students:
                spare = True
        if not spare:
            options.append(option)
    return options


def fewest_rooms(students, sizes, available):
    """The fewest rooms that seat `students` of one paper; None if none can."""
    options = room_options(students, sizes, available)
    if not options:
        return None
    return min(sum(option) for option in options)


def best_combination(group_sizes, sizes, available):
    """One room option per group of students (a group_sizes entry is its
    number of students), so that all groups fit in the rooms there are with
    the fewest rooms, then the fewest empty seats. None if they can't all fit
    or the search grows too big.

    Groups are added one at a time. For each count of rooms used of each size,
    only the best way found to reach it is kept, so the search stays small."""
    # rooms used of each size -> (score, options chosen so far), where score
    # is (rooms, empty seats) and the lower score is the better
    best_for = {tuple([0] * len(sizes)): ((0, 0), [])}
    for students in group_sizes:
        options = room_options(students, sizes, available)
        next_best = {}
        for used, ((rooms, empty), chosen) in best_for.items():
            for option in options:
                now_used = []
                for already, more in zip(used, option):
                    now_used.append(already + more)
                now_used = tuple(now_used)
                too_many = False
                for count, limit in zip(now_used, available):
                    if count > limit:
                        too_many = True
                if too_many:
                    continue

                seats = 0
                for count, size in zip(option, sizes):
                    seats += count * size
                score = (rooms + sum(option), empty + seats - students)
                # on a tie the way found first stays
                if now_used not in next_best or score < next_best[now_used][0]:
                    next_best[now_used] = (score, chosen + [option])
        if not next_best or len(next_best) > MAX_STATES:
            return None
        best_for = next_best

    # the lowest score; on a tie the first one found
    best_score = None
    best_chosen = None
    for score, chosen in best_for.values():
        if best_score is None or score < best_score:
            best_score = score
            best_chosen = chosen
    return best_chosen
