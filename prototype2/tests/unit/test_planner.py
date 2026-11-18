"""Making and writing a plan from picked files (planner.py), without menus or
calendars."""

import subprocess
import sys
from datetime import date

import pytest

import planner
from calendars import ExamCalendar
from conftest import REALISTIC_EXAMPLE, SMALL_EXAMPLE, inputs_of


def run_settings(folder):
    """The settings a run uses when the calendars are left as they start."""
    settings = planner.read_settings(folder / "settings.yaml")
    return ExamCalendar.from_settings(settings).effective_settings()


@pytest.fixture(scope="module")
def realistic_plan(tmp_path_factory):
    """The realistic example's timetable, made once for the tests below."""
    output = tmp_path_factory.mktemp("output")
    selected = inputs_of(REALISTIC_EXAMPLE)
    before = planner.fingerprints(selected)
    plan = planner.generate_timetable(selected, run_settings(REALISTIC_EXAMPLE), output)
    return plan, selected, before


def test_the_timetable_is_written_without_the_seating(realistic_plan):
    plan, _, _ = realistic_plan
    assert len(plan.placements) == 56
    timetable = plan.folder / "timetable"
    assert sorted(path.name for path in timetable.iterdir()) == ["basis.txt", "schedule.csv",
                                                                 "terms.md"]
    # the run's settings and its sources are kept beside it
    assert (plan.folder / "settings.yaml").is_file()
    assert (plan.folder / "sources.json").is_file()


def test_the_seating_passes_the_checker_and_each_yes_makes_a_new_folder(realistic_plan):
    plan, _, _ = realistic_plan
    folder, counts = planner.generate_seating(plan)
    assert counts == {"papers": 56, "room files": 454, "duties": 908, "seats": 8750}
    assert (folder / "daywise_seating_plans").is_dir()
    second, _ = planner.generate_seating(plan)
    assert second != folder


def test_the_input_files_are_never_changed(realistic_plan):
    _, selected, before = realistic_plan
    assert planner.fingerprints(selected) == before


@pytest.mark.parametrize("dataset", [SMALL_EXAMPLE, REALISTIC_EXAMPLE])
def test_the_app_makes_the_same_plan_as_the_command_line(dataset, tmp_path):
    plan = planner.generate_timetable(inputs_of(dataset), run_settings(dataset),
                                      tmp_path / "app")
    app_folder, _ = planner.generate_seating(plan)
    subprocess.run([sys.executable, "-B", str(planner.ENGINE / "main.py"), str(dataset),
                    "--output", str(tmp_path / "command_line")], check=True,
                   capture_output=True)
    command_line_folder = next((tmp_path / "command_line").iterdir())
    app_files = sorted(path.relative_to(app_folder) for path in app_folder.rglob("*.*"))
    command_line_files = sorted(path.relative_to(command_line_folder)
                                for path in command_line_folder.rglob("*.*"))
    assert app_files == command_line_files
    for name in app_files:
        assert (app_folder / name).read_bytes() == (command_line_folder / name).read_bytes(), name


def test_no_plan_gives_the_engines_reason_and_only_why_txt(tmp_path):
    settings = run_settings(SMALL_EXAMPLE)
    settings["end_date"] = date(2026, 11, 4)
    with pytest.raises(planner.NoPlan) as caught:
        planner.generate_timetable(inputs_of(SMALL_EXAMPLE), settings, tmp_path)
    assert "Rule: gap" in str(caught.value)
    assert planner.recovery_for(caught.value) == "dates"
    why = planner.save_failure(caught.value, tmp_path)
    assert [path.name for path in why.parent.iterdir()] == ["why.txt"]
    assert why.read_text(encoding="utf-8").strip() == str(caught.value).strip()


def test_a_missing_file_is_an_input_problem(tmp_path):
    selected = inputs_of(SMALL_EXAMPLE)
    selected["courses"] = SMALL_EXAMPLE / "not-there.csv"
    with pytest.raises(planner.InputProblem) as caught:
        planner.load_selected(selected, run_settings(SMALL_EXAMPLE))
    assert "not-there.csv: file is missing" in str(caught.value)


def test_a_room_name_that_cant_be_a_file_name_is_an_input_problem():
    assert planner.is_safe_file_name("M01")
    for name in ["CON", "a/b", "S01.", "", "..", "lpt1.csv"]:
        assert not planner.is_safe_file_name(name), name


def test_only_a_gap_or_exam_day_problem_sends_the_person_to_the_dates():
    assert planner.recovery_for("No plan possible.\nRule: exam days\n...") == "dates"
    assert planner.recovery_for("No plan possible.\nRule: duties\n...") == "choose"
