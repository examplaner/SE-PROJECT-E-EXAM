"""Show the actual planner responses for the Bash runner's classroom examples."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

WORKFLOW = Path(__file__).resolve().parents[1]
PROTOTYPE = WORKFLOW.parents[1] / "prototype1"
IMPOSSIBLE = PROTOTYPE / "data" / "impossible"


def show(title, expected, actual, passed):
    print(f"\n{title}\nExpected: {expected}\nActual: {actual}")
    print("PASS" if passed else "FAIL")


def validation_demo():
    sys.path.insert(0, str(WORKFLOW))
    import planner

    sample = IMPOSSIBLE / "window_too_short"
    courses = sample / "courses.csv"
    bad = IMPOSSIBLE / "registrations_unknown_course.csv"
    cases = [
        ("1. Select a room list for Teachers", {"teachers": sample / "rooms.csv"},
         "Stage 1", "rooms.csv row 1: header should be teacher_id,rank"),
        ("2. Select registrations and look up their course codes",
         {"registrations": bad, "courses": courses},
         "Stage 2", f"{bad.name} row 50: course code CSE9999 is not in courses.csv"),
        ("3. Replace the registrations with the corrected file",
         {"registrations": sample / "registrations.csv", "courses": courses},
         None, "Selection accepted"),
    ]
    passed_count = 0
    for title, selected, stage, expected in cases:
        try:
            planner.validate_selection(selected)
        except planner.InputProblem as error:
            actual = str(error)
            one_problem = "Input is invalid: 1 problem(s), 1 rule(s) broken." in actual.splitlines()
            passed = stage is not None and actual.startswith(stage) and expected in actual and one_problem
        else:
            actual = "Selection accepted"
            passed = stage is None
        label = f"{stage} - {expected}" if stage else expected
        show(title, label, actual, passed)
        passed_count += passed
    print(f"\n{passed_count}/{len(cases)} validation examples passed.")
    return passed_count == len(cases)


def impossible_demo():
    # Use the expected rules already maintained by the engine tests.
    sys.path.insert(0, str(PROTOTYPE / "tests"))
    from test_no_plan import EXPECTED_RULE

    passed_count = 0
    with TemporaryDirectory() as temp:
        for dataset, rule in EXPECTED_RULE.items():
            output = Path(temp) / dataset
            result = subprocess.run(
                [sys.executable, "-B", str(PROTOTYPE / "main.py"), str(IMPOSSIBLE / dataset),
                 "--output", str(output)], capture_output=True, text=True,
            )
            expected = f"Rule: {rule}"
            files = [path for path in output.rglob("*") if path.is_file()]
            passed = False
            if result.returncode == 2 and len(files) == 1 and files[0].name == "why.txt":
                reason = files[0].read_text(encoding="utf-8").strip()
                passed = expected in reason.splitlines() and reason in result.stdout
            actual = (result.stdout + result.stderr).strip()
            show(dataset, f"exit 2, {expected}, matching why.txt only",
                 f"exit {result.returncode}\n{actual}", passed)
            passed_count += passed
    print(f"\n{passed_count}/{len(EXPECTED_RULE)} impossible datasets passed.")
    return passed_count == len(EXPECTED_RULE)


if __name__ == "__main__":
    if sys.argv[1:] == ["demo"]:
        sys.exit(0 if validation_demo() else 1)
    if sys.argv[1:] == ["impossible"]:
        sys.exit(0 if impossible_demo() else 1)
    sys.exit("Choose demo or impossible.")
