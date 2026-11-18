"""Selection -> calendars -> confirmation -> generation, with back/retry loops."""

import copy
from calendars import ExamCalendar
import planner


def run_workflow(ui, backend=planner):
    selected = {}
    calendar = None
    source_settings = None
    stage = "inputs"
    plan = None
    while True:
        if stage == "inputs":
            plan = None  # Old saved files stay intact, but future runs must be recomputed.
            if not ui.inputs(selected):
                return
            try:
                settings = backend.read_settings(selected["settings"])
            except backend.InputProblem as error:
                ui.message(f"{error}\nTerms: {backend.TERMS}")
                continue
            if calendar is None or settings != source_settings:
                calendar = ExamCalendar.from_settings(settings)
                source_settings = copy.deepcopy(settings)
            stage = "range"
        elif stage in ("range", "exclusions"):
            action, calendar = ui.dates(calendar, stage)
            if stage == "range":
                stage = "inputs" if action == "back" else "exclusions"
            else:
                stage = "range" if action == "back" else "confirm"
        elif stage == "confirm":
            settings = calendar.effective_settings()
            exam_days = (calendar.end - calendar.start).days + 1 - len(settings["holidays"])
            detail = (f"{calendar.start} to {calendar.end}: {exam_days} exam days\n"
                      f"Sessions: {', '.join(map(str, settings['sessions']))}\n"
                      f"Minimum calendar-day gap: {settings['min_gap_days']}; "
                      f"invigilators per room: {settings['invigilators_per_room']}\n"
                      "No returns to inputs and keeps your selections.")
            stage = "generate" if ui.choose("Generate timetable?", ["Yes", "No - back to inputs"], detail) == 0 else "inputs"
        elif stage == "generate":
            ui.report("Generating timetable and checking seating/teacher feasibility...")
            try:
                plan = backend.generate_timetable(selected, calendar.effective_settings())
            except backend.NoPlan as error:
                try:
                    why = backend.save_failure(error)
                    location = f"why.txt path: {why}"
                except OSError as saving_error:
                    location = f"Could not save why.txt: {saving_error}"
                ui.message(f"Why no plan was possible\n{error}\n\n{location}\n"
                           "basis.txt is created when a plan is saved.\n"
                           f"Terms: {backend.TERMS}\nYour selections are kept.")
                if backend.recovery_for(error) == "dates":
                    stage = "range"
                else:
                    choice = ui.choose("What would you like to adjust?",
                                       ["Exam dates", "Input files", "Exit"])
                    if choice == 2:
                        return
                    stage = "range" if choice == 0 else "inputs"
                continue
            except backend.InputProblem as error:
                ui.message(f"{error}\nTerms: {backend.TERMS}\nReturn to inputs; previous choices are kept.")
                stage = "inputs"
                continue
            except (OSError, RuntimeError) as error:
                ui.message(f"Generation did not complete: {error}\nTerms: {backend.TERMS}")
                choice = ui.choose("Retry or go back?", ["Retry generation", "Back to inputs", "Exit"])
                if choice == 2:
                    return
                stage = "generate" if choice == 0 else "inputs"
                continue
            except KeyboardInterrupt:
                ui.message("Generation interrupted. Selections kept; returning to exam dates.")
                stage = "range"
                continue
            ui.report(f"Timetable saved and checked: {plan.folder / 'timetable' / 'schedule.csv'}\n"
                      f"basis.txt path: {plan.folder / 'timetable' / 'basis.txt'}\n"
                      f"Terms: {plan.folder / 'timetable' / 'terms.md'}")
            stage = "seating"
        elif stage == "seating":
            if ui.choose("Generate seating plan and teacher duties?", ["Yes", "No - back to inputs"],
                         f"Timetable: {plan.folder / 'timetable' / 'schedule.csv'}\n"
                         "The saved timetable remains available if you go back.") != 0:
                stage = "inputs"
                continue
            ui.report("Writing and checking the seating plan and teacher duties...")
            try:
                folder, counts = backend.generate_seating(plan)
            except (OSError, RuntimeError) as error:
                ui.message(f"Seating export did not complete: {error}\n"
                           f"The timetable is still at {plan.folder / 'timetable' / 'schedule.csv'}\n"
                           f"Terms: {backend.TERMS}")
                continue
            ui.report(f"Seating plan: {folder / 'daywise_seating_plans'}\n"
                      f"Teacher duties: {folder / 'duties.csv'}\n"
                      f"basis.txt path: {folder / 'basis.txt'}\nTerms: {folder / 'terms.md'}\n"
                      f"Plan check passed: {counts['papers']} papers, {counts['room files']} room files, "
                      f"{counts['seats']} seats, {counts['duties']} duties.")
            if ui.choose("Plan saved", ["Back to input selection", "Exit"], str(folder)) == 1:
                return
            stage = "inputs"
