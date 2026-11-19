"""The steps of the app, in order:

    inputs -> exam range -> no-exam days -> "make the timetable?"
           -> "write the seating plan and teacher duties?"

Every step can go back without losing what was chosen, and a failure shows
the engine's reason and returns to the dates or the inputs instead of
starting over.

ui is the terminal module in the app (a fake one in the tests): it asks and
shows, and checks each file as it is picked. backend is the planner module:
it checks the files together, and makes and writes the plan.
"""

from calendars import ExamCalendar


def run_workflow(ui, backend):
    # {input key: Path}; kept for the whole run, so going back loses nothing
    selected = {}
    exam_calendar = None
    file_settings = None
    plan = None
    step = "inputs"
    while True:
        if step == "inputs":
            if not ui.pick_inputs(selected):
                return
            try:
                settings = backend.read_settings(selected["settings"])
                # the checks across files, before the calendars open
                backend.load_selected(selected, settings)
            except backend.InputProblem as error:
                ui.pause(f"{error}\nTerms: {backend.TERMS}")
                continue
            # a new or changed settings file starts the calendars again
            if exam_calendar is None or settings != file_settings:
                exam_calendar = ExamCalendar.from_settings(settings)
                file_settings = settings
            step = "range"

        elif step == "range":
            action, exam_calendar = ui.pick_dates(exam_calendar, "range")
            step = "inputs" if action == "back" else "exclusions"

        elif step == "exclusions":
            action, exam_calendar = ui.pick_dates(exam_calendar, "exclusions")
            step = "range" if action == "back" else "confirm"

        elif step == "confirm":
            if ui.confirm("Make the timetable now?", run_summary(exam_calendar)):
                step = "timetable"
            else:
                step = "inputs"

        elif step == "timetable":
            plan, step = make_timetable(ui, backend, selected, exam_calendar)

        elif step == "seating":
            step = write_seating(ui, backend, plan)

        elif step == "exit":
            return


def run_summary(exam_calendar):
    """What the run will use, shown before the timetable is made."""
    settings = exam_calendar.effective_settings()
    # effective_settings() lists every no-exam day of the range as a holiday
    days = (exam_calendar.end - exam_calendar.start).days + 1 - len(settings["holidays"])
    sessions = ", ".join(str(session) for session in settings["sessions"])
    return (f"{exam_calendar.start} to {exam_calendar.end}: {days} exam days\n"
            f"Sessions: {sessions}\n"
            f"Minimum calendar-day gap: {settings['min_gap_days']}; "
            f"invigilators per room: {settings['invigilators_per_room']}\n"
            f"No goes back to the inputs and keeps your choices.")


def make_timetable(ui, backend, selected, exam_calendar):
    """Returns (the plan or None, the next step)."""
    ui.show("Making the timetable and checking seats and teachers...")
    try:
        plan = backend.generate_timetable(selected, exam_calendar.effective_settings())
    except backend.NoPlan as error:
        try:
            location = f"Reason saved in: {backend.save_failure(error)}"
        except OSError as saving_error:
            location = f"Could not save why.txt: {saving_error}"
        ui.pause(f"{error}\n{location}\nTerms: {backend.TERMS}\nYour choices are kept.")
        # a gap or exam-day problem is fixed with other dates
        if backend.recovery_for(error) == "dates":
            return None, "range"
        next_steps = ["range", "inputs", "exit"]
        answer = ui.choose("What would you like to change?", ["Exam dates", "Input files", "Exit"])
        return None, next_steps[answer]
    except backend.InputProblem as error:
        ui.pause(f"{error}\nTerms: {backend.TERMS}\nBack to the inputs; your choices are kept.")
        return None, "inputs"
    except (OSError, RuntimeError) as error:
        ui.pause(f"The timetable was not made: {error}\nTerms: {backend.TERMS}")
        next_steps = ["timetable", "inputs", "exit"]
        answer = ui.choose("Try again or go back?", ["Try again", "Back to inputs", "Exit"])
        return None, next_steps[answer]
    except KeyboardInterrupt:
        ui.pause("Stopped. Your choices are kept; back to the exam dates.")
        return None, "range"

    ui.show(f"Timetable saved and checked: {plan.folder / 'timetable' / 'schedule.csv'}\n"
            f"Basis: {plan.folder / 'timetable' / 'basis.txt'}\n"
            f"Terms: {plan.folder / 'timetable' / 'terms.md'}")
    return plan, "seating"


def write_seating(ui, backend, plan):
    """Returns the next step."""
    timetable = plan.folder / "timetable" / "schedule.csv"
    if not ui.confirm("Write the seating plan and teacher duties?",
                      f"Timetable: {timetable}\nThe saved timetable stays if you go back."):
        return "inputs"
    ui.show("Writing the seating plan and checking it with the checker...")
    try:
        folder, counts = backend.generate_seating(plan)
    except (OSError, RuntimeError) as error:
        ui.pause(f"The seating plan was not saved: {error}\n"
                 f"The timetable is still at {timetable}\nTerms: {backend.TERMS}")
        return "seating"
    ui.show(f"Seating plan: {folder / 'daywise_seating_plans'}\n"
            f"Teacher duties: {folder / 'duties.csv'}\n"
            f"Basis: {folder / 'basis.txt'}\n"
            f"Terms: {folder / 'terms.md'}\n"
            f"Plan check passed: {counts['papers']} papers, {counts['room files']} room files, "
            f"{counts['seats']} seats, {counts['duties']} duties.")
    next_steps = ["inputs", "exit"]
    answer = ui.choose(f"Plan saved in {folder}", ["Back to the inputs", "Exit"])
    return next_steps[answer]
