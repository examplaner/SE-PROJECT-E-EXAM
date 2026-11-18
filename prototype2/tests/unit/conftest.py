"""What the unit tests share. Run from prototype2/:

    python -m pytest tests/unit
"""

import sys
from pathlib import Path

PROTOTYPE = Path(__file__).resolve().parents[2]
# the app's modules sit in prototype2/
sys.path.insert(0, str(PROTOTYPE))

# 16 students, 3 rooms, one week: a copy of prototype1's data/tiny
SMALL_EXAMPLE = PROTOTYPE / "data" / "small_example"
# 1,600 students, 36 rooms, three weeks: a copy of prototype1's data/main
REALISTIC_EXAMPLE = PROTOTYPE / "data" / "realistic_example"


def inputs_of(folder):
    """The nine inputs of a dataset folder, as the app's menu would pick them."""
    selected = {}
    for key in ["teachers", "courses", "sections", "registrations", "rooms", "teaching"]:
        selected[key] = folder / f"{key}.csv"
    selected["students"] = folder / "sections"
    selected["settings"] = folder / "settings.yaml"
    selected["constraints"] = folder / "constraints.yaml"
    return selected
