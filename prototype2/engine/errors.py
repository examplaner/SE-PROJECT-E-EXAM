"""The error raised when no plan is possible (model spec section 12). It has a
file of its own because schedule.py, seat.py and duties.py all raise it, and
they import each other."""


class NoPlan(Exception):
    """str(error) is the reason, as printed and written to why.txt."""
