"""Exercise real Tk widgets and save two new, window-only preview images."""

from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from calendars import CalendarDialog, ExamCalendar
import planner
from PIL import ImageGrab

root = Path(__file__).resolve().parents[3]
settings = planner.read_settings(root / "prototype1/data/main/settings.yaml")
state = ExamCalendar.from_settings(settings)
preview = Path(__file__).resolve().parents[1] / "review"
preview.mkdir()  # Fail rather than overwrite a previous review's images.


def capture(dialog, name):
    dialog.root.update()
    dialog.root.lift()
    dialog.root.update()
    x, y = dialog.root.winfo_rootx(), dialog.root.winfo_rooty()
    width, height = dialog.root.winfo_width(), dialog.root.winfo_height()
    with (preview / name).open("xb") as stream:
        ImageGrab.grab(bbox=(x, y, x + width, y + height), all_screens=True).save(stream, format="PNG")


dialog = CalendarDialog(state, "range")
try:
    capture(dialog, "range.png")
    dialog.year.set(2028)
    dialog.month.set(2)
    dialog.redraw()
    assert any(widget.cget("text") == "29" for widget in dialog.grid.winfo_children())
    dialog.select(date(2028, 2, 29))
    dialog.select(date(2028, 3, 10))
    dialog.finish("continue")
    assert dialog.result[1].start == date(2028, 2, 29)
    assert dialog.result[1].end == date(2028, 3, 10)
finally:
    try:
        dialog.root.destroy()
    except Exception:
        pass

dialog = CalendarDialog(state, "exclusions")
try:
    capture(dialog, "holidays.png")
    dialog.select(date(2026, 11, 11))
    dialog.finish("back")
    assert not dialog.result[1].excluded(date(2026, 11, 11))
    assert state.excluded(date(2026, 11, 11))
finally:
    try:
        dialog.root.destroy()
    except Exception:
        pass

print("Real Tk windows passed: leap date, range selection, holiday toggle and Back.")
print("Window previews:", preview)
