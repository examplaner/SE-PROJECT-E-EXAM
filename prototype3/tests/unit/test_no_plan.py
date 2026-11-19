"""When no plan is possible (model spec section 12): each folder in
data/impossible/ breaks one thing, and main.py exits with 2, names the rule,
and writes only why.txt."""

import pytest

from conftest import IMPOSSIBLE_DATASETS, SMALL_DATASET, run_main

# folder in data/impossible/ -> (the rule its message names, a line it holds)
EXPECTED = {
    "no_exam_days": ("exam days", "settings.yaml gives no exam day"),
    "window_too_short": ("gap", "at most 2 papers fit"),
    "paper_too_big": ("seats", "The only room gives 12 seats to one paper"),
    "no_day_fits": ("paper placement",
                    "  - teachers: 10 sessions would need more teachers than the 9 there are "
                    "(5 per room)"),
    "waiting_paper": ("duty room", "teachers have no room they may invigilate for their "
                                   "paper: T005 (CSE2001)."),
    "duty_room_full": ("duty room", "They are full of other teachers who can't sit "
                                    "anywhere else."),
    "too_few_teachers": ("duties", "Every room needs 3 teachers."),
}


def test_every_impossible_folder_has_a_test():
    folders = {path.name for path in IMPOSSIBLE_DATASETS.iterdir() if path.is_dir()}
    assert folders == set(EXPECTED)


@pytest.mark.parametrize("dataset", sorted(EXPECTED))
def test_impossible_dataset_says_why(dataset, tmp_path, capsys):
    rule, line = EXPECTED[dataset]
    code, printed, folder = run_main(IMPOSSIBLE_DATASETS / dataset, tmp_path / "out", capsys)
    assert code == 2, printed
    # only why.txt: never half a plan
    assert [path.name for path in folder.iterdir()] == ["why.txt"]
    why = (folder / "why.txt").read_text(encoding="utf-8")
    assert why.splitlines()[:2] == ["No plan possible.", f"Rule: {rule}"]
    assert line in why
    assert why in printed


def test_files_with_only_headers_have_no_papers(small_copy, tmp_path, capsys):
    # with no sections, students or courses every check passes, and
    # there is nothing to schedule
    for name in ["sections.csv", "courses.csv", "registrations.csv", "teaching.csv"]:
        path = small_copy / name
        header = path.read_text(encoding="utf-8").splitlines()[0]
        path.write_text(header + "\n", encoding="utf-8")
    for roster in (small_copy / "sections").iterdir():
        roster.unlink()
    (small_copy / "constraints.yaml").write_text("", encoding="utf-8")
    code, printed, folder = run_main(small_copy, tmp_path / "out", capsys)
    assert code == 2, printed
    assert "Rule: papers" in printed
    assert [path.name for path in folder.iterdir()] == ["why.txt"]


def test_a_valid_input_writes_no_why_txt(tmp_path, capsys):
    code, _, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    assert code == 0
    assert not (folder / "why.txt").exists()
