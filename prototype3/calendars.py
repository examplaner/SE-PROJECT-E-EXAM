"""The exam range and the no-exam days, chosen in two Tkinter calendars.

ExamCalendar holds the dates in memory; the settings file is never written.
Days the settings exclude (a weekday not in exam_weekdays, a holiday) start
out marked as no-exam days, and any day in the range can be switched.
"""

import calendar
import copy
import datetime
import functools
import tkinter
from dataclasses import dataclass, field
from tkinter import ttk

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def as_date(value):
    """A YAML date or 'YYYY-MM-DD' text as a date."""
    # a datetime is a kind of date in Python, so check the exact type
    if type(value) is datetime.date:
        return value
    return datetime.date.fromisoformat(str(value))


@dataclass
class ExamCalendar:
    # the settings as read from the file; never changed
    settings: dict
    start: datetime.date
    end: datetime.date
    # day -> True (no exam) or False (exam day) for days switched by hand
    switched: dict = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings):
        return cls(copy.deepcopy(settings), as_date(settings["start_date"]),
                   as_date(settings["end_date"]))

    def excluded(self, day):
        """True if no exam may be written on this day."""
        if day in self.switched:
            return self.switched[day]
        holidays = {as_date(value) for value in (self.settings.get("holidays") or [])}
        return WEEKDAYS[day.weekday()] not in self.settings["exam_weekdays"] or day in holidays

    def switch(self, day):
        if not self.start <= day <= self.end:
            raise ValueError("Choose a date inside the exam range.")
        self.switched[day] = not self.excluded(day)

    def effective_settings(self):
        """The settings for this run: the chosen range, and every no-exam day
        in it listed as a holiday, so any day can be allowed or excluded."""
        if self.start > self.end:
            raise ValueError("The end date must be on or after the start date.")
        settings = copy.deepcopy(self.settings)
        settings["start_date"] = self.start
        settings["end_date"] = self.end
        settings["exam_weekdays"] = list(WEEKDAYS)
        holidays = []
        day = self.start
        while day <= self.end:
            if self.excluded(day):
                holidays.append(day)
            day += datetime.timedelta(days=1)
        settings["holidays"] = holidays
        return settings


def choose_dates(exam_calendar, mode):
    """Show one calendar window. mode: "range" (choose the first and last exam
    day) or "exclusions" (switch no-exam days). Returns ("continue" or
    "back", the calendar to use next)."""
    return CalendarDialog(exam_calendar, mode).show()


class CalendarDialog:
    """One calendar window. It works on a copy of the dates. Back, Continue
    and closing the window all keep what was clicked, except a backwards
    range: then Continue is refused, and Back keeps the dates as they were."""

    def __init__(self, exam_calendar, mode):
        self.original = exam_calendar
        self.state = copy.deepcopy(exam_calendar)
        self.mode = mode
        self.result = ("back", exam_calendar)

        self.root = tkinter.Tk()
        if mode == "range":
            self.root.title("Exam date range")
        else:
            self.root.title("No-exam days")
        self.root.resizable(False, False)
        # closing the window with its X, or pressing Escape, goes back
        self.root.protocol("WM_DELETE_WINDOW", self.go_back)
        self.root.bind("<Escape>", self.go_back)
        self.month = tkinter.IntVar(value=exam_calendar.start.month)
        self.year = tkinter.IntVar(value=exam_calendar.start.year)
        # which end of the range the next click sets
        self.endpoint = tkinter.StringVar(value="start")
        self.status = tkinter.StringVar()
        self.description = tkinter.StringVar()
        self.build_window()
        self.redraw()

    def build_window(self):
        frame = ttk.Frame(self.root, padding=18)
        frame.pack()
        ttk.Label(frame, text=self.root.title(), font="TkHeadingFont").pack(anchor="w")
        ttk.Label(frame, textvariable=self.description).pack(anchor="w", pady=(8, 12))
        if self.mode == "range":
            endpoints = ttk.Frame(frame)
            endpoints.pack(fill="x")
            ttk.Radiobutton(endpoints, text="Choose start date", variable=self.endpoint,
                            value="start").pack(side="left", padx=(0, 16))
            ttk.Radiobutton(endpoints, text="Choose end date", variable=self.endpoint,
                            value="end").pack(side="left")
        else:
            ttk.Label(frame, text="Red = no exam. Click a date to exclude it or allow it "
                                  "again.").pack()

        navigation = ttk.Frame(frame)
        navigation.pack(fill="x", pady=12)
        ttk.Button(navigation, text="<", width=4, command=self.previous_month).pack(side="left")
        ttk.Label(navigation, text="Month").pack(side="left", padx=(8, 3))
        ttk.Spinbox(navigation, from_=1, to=12, width=4,
                    textvariable=self.month).pack(side="left")
        ttk.Label(navigation, text="Year").pack(side="left", padx=(8, 3))
        ttk.Spinbox(navigation, from_=1, to=9999, width=6,
                    textvariable=self.year).pack(side="left")
        ttk.Button(navigation, text="Show", command=self.redraw).pack(side="left", padx=8)
        ttk.Button(navigation, text=">", width=4, command=self.next_month).pack(side="right")

        self.grid = ttk.Frame(frame)
        self.grid.pack()
        ttk.Label(frame, textvariable=self.status, wraplength=480).pack(fill="x", pady=12)
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions, text="Back", command=self.go_back).pack(side="left")
        ttk.Button(actions, text="Continue", command=self.go_on).pack(side="right")

    def shown_month(self):
        """(year, month) typed in the boxes, or None if they are not a month."""
        try:
            year = int(self.year.get())
            month = int(self.month.get())
            # raises ValueError if this is not a real month
            datetime.date(year, month, 1)
        except (ValueError, tkinter.TclError):
            self.status.set("Enter a month from 1 to 12 and a year from 1 to 9999, then Show.")
            return None
        return year, month

    def move(self, months):
        shown = self.shown_month()
        if shown is None:
            return
        year, month = shown
        # months counted from January of year 1
        number = (year - 1) * 12 + (month - 1) + months
        if 0 <= number < 9999 * 12:
            self.year.set(number // 12 + 1)
            self.month.set(number % 12 + 1)
            self.redraw()

    def select(self, day):
        if self.mode == "range":
            if self.endpoint.get() == "start":
                self.state.start = day
                self.endpoint.set("end")
            else:
                self.state.end = day
        else:
            self.state.switch(day)
        self.redraw()

    def redraw(self):
        shown = self.shown_month()
        if shown is None:
            return
        year, month = shown
        for widget in self.grid.winfo_children():
            widget.destroy()
        self.description.set(f"{calendar.month_name[month]} {year}\n"
                             f"Range: {self.state.start} to {self.state.end}")
        for column, name in enumerate(WEEKDAYS):
            ttk.Label(self.grid, text=name, anchor="center", width=8).grid(row=0, column=column)
        for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for column, number in enumerate(week):
                # 0 is a day of the next or previous month
                if number == 0:
                    continue
                day = datetime.date(year, month, number)
                self.day_cell(day).grid(row=row, column=column, padx=2, pady=2)
        if self.state.start > self.state.end:
            self.status.set("Choose an end date on or after the start date before continuing.")
        else:
            self.status.set("These dates are for this run only. The settings file stays "
                            "unchanged.")

    def day_cell(self, day):
        """One day of the month: a label that reacts to a click. Not a button,
        because macOS draws buttons itself and ignores their colour."""
        inside = self.state.start <= day <= self.state.end
        cell = tkinter.Label(self.grid, text=str(day.day), width=7, height=2,
                             relief="raised", borderwidth=1)
        if self.mode == "exclusions" and not inside:
            # outside the range: shown grey, and a click does nothing
            cell.configure(foreground="grey")
            return cell
        if self.mode == "exclusions" and self.state.excluded(day):
            cell.configure(background="#a32929", foreground="white")
        elif self.mode == "range" and inside:
            cell.configure(background="#245a81", foreground="white")
        # partial() fixes this cell's day now; Tkinter adds the click event
        # when it calls click_day()
        cell.bind("<Button-1>", functools.partial(self.click_day, day))
        return cell

    # Tkinter calls a button's command with nothing, and a key's or a click's
    # handler with the event, which these don't need
    def go_back(self, event=None):
        self.finish("back")

    def go_on(self):
        self.finish("continue")

    def previous_month(self):
        self.move(-1)

    def next_month(self):
        self.move(1)

    def click_day(self, day, event):
        self.select(day)

    def finish(self, action):
        if self.state.start > self.state.end:
            if action == "continue":
                self.status.set("The end date must be on or after the start date.")
                return
            self.result = (action, self.original)
        else:
            self.result = (action, self.state)
        self.root.destroy()

    def show(self):
        try:
            self.root.mainloop()
            return self.result
        finally:
            # closing the window may have destroyed it already
            try:
                self.root.destroy()
            except tkinter.TclError:
                pass
