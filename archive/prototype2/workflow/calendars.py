"""Two calendar windows backed by one editable, in-memory exam calendar."""

import calendar
import copy
from dataclasses import dataclass, field
from datetime import date, timedelta
import tkinter as tk
from tkinter import ttk

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def as_date(value):
    return value if type(value) is date else date.fromisoformat(str(value))


@dataclass
class ExamCalendar:
    settings: dict
    start: date
    end: date
    overrides: dict = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings):
        return cls(copy.deepcopy(settings), as_date(settings["start_date"]),
                   as_date(settings["end_date"]))

    def excluded(self, day):
        holidays = {as_date(value) for value in (self.settings.get("holidays") or [])}
        default = WEEKDAYS[day.weekday()] not in self.settings["exam_weekdays"] or day in holidays
        return self.overrides.get(day, default)

    def toggle(self, day):
        if not self.start <= day <= self.end:
            raise ValueError("Select a date inside the exam range.")
        self.overrides[day] = not self.excluded(day)

    def effective_settings(self):
        if self.start > self.end:
            raise ValueError("The end date must be on or after the start date.")
        settings = copy.deepcopy(self.settings)
        settings.update(start_date=self.start, end_date=self.end,
                        exam_weekdays=list(WEEKDAYS))
        # Expand weekday restrictions into specific dates so any day can be toggled.
        settings["holidays"] = [self.start + timedelta(days=offset)
                                for offset in range((self.end - self.start).days + 1)
                                if self.excluded(self.start + timedelta(days=offset))]
        return settings


class CalendarDialog:
    """Range mode chooses endpoints; exclusions mode toggles individual dates."""

    def __init__(self, state, mode):
        self.original = state
        self.state = copy.deepcopy(state)
        self.mode = mode
        self.result = ("back", state)
        self.root = tk.Tk()
        self.root.title("Exam date range" if mode == "range" else "No-exam days")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.finish("back"))
        self.root.bind("<Escape>", lambda event: self.finish("back"))
        self.month = tk.IntVar(value=state.start.month)
        self.year = tk.IntVar(value=state.start.year)
        self.endpoint = tk.StringVar(value="start")
        self.status = tk.StringVar()
        self.description = tk.StringVar()
        frame = ttk.Frame(self.root, padding=18)
        frame.pack()
        ttk.Label(frame, text=self.root.title(), font=("Segoe UI", 14, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.description).pack(anchor="w", pady=(8, 12))
        if mode == "range":
            endpoints = ttk.Frame(frame)
            endpoints.pack(fill="x")
            for value, label in [("start", "Choose start date"), ("end", "Choose end date")]:
                ttk.Radiobutton(endpoints, text=label, variable=self.endpoint,
                                value=value).pack(side="left", padx=(0, 16))
        else:
            ttk.Label(frame, text="Red = no exam. Click a date to exclude it or allow it again.").pack()
        navigation = ttk.Frame(frame)
        navigation.pack(fill="x", pady=12)
        ttk.Button(navigation, text="<", width=4, command=lambda: self.move(-1)).pack(side="left")
        ttk.Label(navigation, text="Month").pack(side="left", padx=(8, 3))
        ttk.Spinbox(navigation, from_=1, to=12, width=4, textvariable=self.month).pack(side="left")
        ttk.Label(navigation, text="Year").pack(side="left", padx=(8, 3))
        ttk.Spinbox(navigation, from_=1, to=9999, width=6, textvariable=self.year).pack(side="left")
        ttk.Button(navigation, text="Show", command=self.redraw).pack(side="left", padx=8)
        ttk.Button(navigation, text=">", width=4, command=lambda: self.move(1)).pack(side="right")
        self.grid = ttk.Frame(frame)
        self.grid.pack()
        ttk.Label(frame, textvariable=self.status, wraplength=480).pack(fill="x", pady=12)
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions, text="Back", command=lambda: self.finish("back")).pack(side="left")
        ttk.Button(actions, text="Continue", command=lambda: self.finish("continue")).pack(side="right")
        self.redraw()

    def displayed_month(self):
        try:
            year, month = int(self.year.get()), int(self.month.get())
            date(year, month, 1)
            return year, month
        except (ValueError, tk.TclError):
            self.status.set("Enter a month from 1 to 12 and a year from 1 to 9999, then Show.")
            return None

    def move(self, amount):
        current = self.displayed_month()
        if current is None:
            return
        year, month = current
        number = (year - 1) * 12 + month - 1 + amount
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
            self.state.toggle(day)
        self.redraw()

    def redraw(self):
        current = self.displayed_month()
        if current is None:
            return
        year, month = current
        for widget in self.grid.winfo_children():
            widget.destroy()
        self.description.set(f"{calendar.month_name[month]} {year}\n"
                             f"Range: {self.state.start} to {self.state.end}")
        for column, label in enumerate(WEEKDAYS):
            ttk.Label(self.grid, text=label, anchor="center", width=8).grid(row=0, column=column)
        for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for column, number in enumerate(week):
                if not number:
                    continue
                day = date(year, month, number)
                inside = self.state.start <= day <= self.state.end
                button = tk.Button(self.grid, text=str(number), width=7, height=2,
                                   command=lambda value=day: self.select(value))
                if self.mode == "exclusions" and not inside:
                    button.configure(state="disabled")
                elif self.mode == "exclusions" and self.state.excluded(day):
                    button.configure(background="#a32929", foreground="white")
                elif self.mode == "range" and inside:
                    button.configure(background="#245a81", foreground="white")
                button.grid(row=row, column=column, padx=2, pady=2)
        if self.state.start > self.state.end:
            self.status.set("Choose an end date on or after the start date before continuing.")
        else:
            self.status.set("These choices apply to this run. The original settings file stays unchanged.")

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
            try:
                self.root.destroy()
            except tk.TclError:
                pass


def choose_dates(state, mode):
    return CalendarDialog(state, mode).show()
