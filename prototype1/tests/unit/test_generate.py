"""The dataset generator (tools/generate_data.py) writes the datasets in data/."""

import random
import sys

import pytest

from conftest import PROTOTYPE, REALISTIC_DATASET, SMALL_DATASET

# the generator is a script in tools/
sys.path.insert(0, str(PROTOTYPE / "tools"))
import generate_data  # noqa: E402


@pytest.mark.parametrize("design, dataset", [(generate_data.TINY, SMALL_DATASET),
                                             (generate_data.MAIN, REALISTIC_DATASET)])
def test_the_generator_writes_the_files_in_data(design, dataset, tmp_path):
    out_dir = tmp_path / design["name"]
    generate_data.build_dataset(design, out_dir)
    written = sorted(path.relative_to(out_dir) for path in out_dir.rglob("*") if path.is_file())
    there = sorted(path.relative_to(dataset) for path in dataset.rglob("*") if path.is_file())
    assert written == there
    # line by line, so a checkout with other line endings still matches
    for name in written:
        new_lines = (out_dir / name).read_text(encoding="utf-8").splitlines()
        assert new_lines == (dataset / name).read_text(encoding="utf-8").splitlines(), name
    assert generate_data.check_folder(out_dir) == []


def test_elective_sizes_must_add_up():
    with pytest.raises(generate_data.DesignError):
        generate_data.allocate_electives("X", ["s1", "s2"], {"e1": 1}, 1, random.Random(1))


def test_two_electives_per_student_are_always_different():
    students = [f"s{n}" for n in range(10)]
    chosen = generate_data.allocate_electives("X", students, {"a": 8, "b": 7, "c": 5}, 2,
                                              random.Random(3))
    for electives in chosen.values():
        assert len(electives) == 2 and electives[0] != electives[1]
