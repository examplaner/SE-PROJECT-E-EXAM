"""The plan folder main.py writes (model spec section 11)."""

import csv

import writer
from conftest import SMALL_DATASET, run_main


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.reader(file))


def test_the_plan_folder_holds_the_plan_and_nothing_else(tmp_path, capsys):
    code, printed, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    assert code == 0, printed
    names = sorted(path.name for path in folder.iterdir())
    assert names == ["basis.txt", "daywise_seating_plans", "duties.csv", "schedule.csv",
                     "terms.md"]
    assert f"Wrote {folder}" in printed


def test_schedule_csv(tmp_path, capsys):
    _, printed, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    rows = read_csv(folder / "schedule.csv")
    assert rows[0] == ["date", "session", "paper_id", "course_codes", "students"]
    # a paper's course codes are joined with ';'
    assert rows[1] == ["2026-11-02", "morning", "CSE2001", "CSE2001;CSE2003", "16"]
    assert len(rows) == 1 + 7
    assert "Fullest session: 2026-11-02 morning, 16 of 45 seats (29 left)." in printed


def test_one_room_csv_per_room_in_use_drawn_like_the_room(tmp_path, capsys):
    _, printed, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    room_files = sorted(folder.glob("daywise_seating_plans/*/*/*.csv"))
    assert len(room_files) == 7
    assert "Seating: 7 room files (1 with two papers)." in printed

    rows = read_csv(folder / "daywise_seating_plans" / "2026-11-02" / "morning" / "S01.csv")
    # no header; one CSV row per row of seats, front first; blank = empty seat
    assert len(rows) == 6 and all(len(row) == 3 for row in rows)
    assert rows[0] == ["CSE2001:BT2CSE0001", "", "CSE2001:BT2CSE0007"]


def test_duties_csv_has_two_teachers_per_room(tmp_path, capsys):
    _, printed, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    rows = read_csv(folder / "duties.csv")
    assert rows[0] == ["date", "session", "room_id", "teacher_id"]
    assert len(rows) - 1 == 2 * 7
    assert "Duties: 14. Each regular teacher has 1 to 2; PhD scholars have 0." in printed


def test_basis_txt_is_printed_too_and_terms_md_is_copied(tmp_path, capsys):
    _, printed, folder = run_main(SMALL_DATASET, tmp_path / "out", capsys)
    lines = (folder / "basis.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("Timetable basis: biggest papers first")
    assert lines[1] == ("Seating basis: one paper per room, with the mix of room sizes that "
                        "needs the fewest rooms; 6 rooms hold one paper and 1 holds two (two "
                        "papers' leftovers joined, or mixed where the rooms ran out).")
    assert lines[2] == writer.TERMS_LINE
    for line in lines:
        assert line in printed
    terms = (folder / "terms.md").read_text(encoding="utf-8")
    assert terms == writer.TERMS_FILE.read_text(encoding="utf-8")


def test_a_second_run_in_the_same_second_gets_its_own_folder(tmp_path):
    first = writer.new_plan_folder(tmp_path)
    second = writer.new_plan_folder(tmp_path)
    assert first != second
    if first.name[:19] == second.name[:19]:
        assert second.name == first.name + "_2"
