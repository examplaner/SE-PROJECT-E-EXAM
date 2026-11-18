"""Turn an input folder into an exam plan (model spec section 4).

    python main.py data/tiny [--output output]

Exit codes:
    0  a plan was written: schedule.csv, the room CSVs, duties.csv, basis.txt
       and terms.md, in a new folder named by the time of the run
    1  the input is invalid; every problem is printed
    2  no plan is possible; the reason is printed and written to why.txt,
       the only file in the new folder
"""

import argparse
import sys

import duties
import loader
import schedule
import seat
import validate
import writer
from errors import NoPlan
from exam import build_exam


def main(argv=None):
    parser = argparse.ArgumentParser(description="Turn an input folder into an exam plan.")
    parser.add_argument("input_dir", help="folder with the input files")
    parser.add_argument("--output", default="output",
                        help="where plan folders go (default: output/)")
    args = parser.parse_args(argv)

    problems = validate.check_folder(args.input_dir)
    if problems:
        print(validate.format_report(problems))
        print("\nFix these first. The checks on the data inside the files "
              "run once every file can be read.")
        return 1
    data = loader.load(loader.input_paths(args.input_dir))
    problems = validate.check_data(data)
    if problems:
        print(validate.format_report(problems))
        return 1
    print(summary(data))

    # steps 4, 5 and 6 all run before anything is written
    exam = build_exam(data)
    try:
        placements, way, failed = schedule.make_schedule(exam)
        if not placements:
            # only an input with no students at all gets here
            raise NoPlan("No plan possible.\n"
                         "Rule: papers\n"
                         "courses.csv has no course codes, so there is nothing to schedule.")
        seating = seat.make_seating(placements, exam)
        duty_rows = duties.make_duties(seating, exam)
    except NoPlan as reason:
        folder = writer.new_plan_folder(args.output)
        path = writer.write_why(str(reason), folder)
        print(reason)
        print(f"Wrote {path}")
        return 2

    folder = writer.new_plan_folder(args.output)
    writer.write_schedule(placements, folder / "schedule.csv")
    room_files = writer.write_seating(seating, folder)
    writer.write_duties(duty_rows, folder / "duties.csv")
    basis = [schedule.basis_line(way, failed), seat.basis_line(seating)]
    for line in writer.write_basis(basis, folder):
        print(line)
    print_numbers(placements, seating, duty_rows, room_files, exam)
    print(f"Wrote {folder}")
    return 0


def summary(data):
    """One line with the sizes of a valid input."""
    groups = data["constraints"].get("same_paper") or []
    papers = len(data["courses"])
    for group in groups:
        papers -= len(group) - 1
    return (f"Input OK: {len(data['sections'])} sections, "
            f"{len(data['students'])} students, "
            f"{len(data['courses'])} course codes ({papers} papers), "
            f"{len(data['rooms'])} rooms, {len(data['teachers'])} teachers.")


def print_numbers(placements, seating, duty_rows, room_files, exam):
    """How full the plan is: days, the fullest session, rooms and duties."""
    days = sorted({placement.date for placement in placements})
    print(f"Scheduled {len(placements)} papers on {len(days)} days, {days[0]} to {days[-1]}.")

    day, session, students, limit = schedule.fullest_session(placements, exam)
    print(f"Fullest session: {day} {session}, {students} of {limit} seats "
          f"({limit - students} left).")

    # the first slot with the most rooms
    busiest_slot = None
    busiest_rooms = 0
    for slot, plans in seating.items():
        if busiest_slot is None or len(plans) > busiest_rooms:
            busiest_slot = slot
            busiest_rooms = len(plans)
    day, session = busiest_slot
    print(f"Seating: {room_files} room files ({seat.two_paper_rooms(seating)} with two "
          f"papers). Most rooms in one slot: {busiest_rooms} of {len(exam.rooms)} "
          f"({day} {session}).")

    numbers = duties.duty_summary(duty_rows, exam)
    print(f"Duties: {len(duty_rows)}. Each regular teacher has {numbers['fewest']} to "
          f"{numbers['most']}; PhD scholars have {numbers['phd_duties']}. Teachers with "
          f"both shifts on one day: {numbers['double_days']} times.")


if __name__ == "__main__":
    sys.exit(main())
