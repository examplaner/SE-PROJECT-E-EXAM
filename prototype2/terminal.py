"""How the app asks and shows things: arrow-key menus and yes/no questions
with questionary, Tkinter pickers and calendars. Up/Down move, Enter chooses,
and the menus go round at the ends. Ctrl+C in a menu goes back without losing
a choice.
"""

import questionary

import calendars
import inputs


def ask(message, choices, default=None):
    """A menu. choices: (title, value, description) tuples; the description
    shows under the highlighted row. default: the value highlighted first.
    Returns the chosen value, or None after Ctrl+C."""
    options = []
    for title, value, description in choices:
        options.append(questionary.Choice(title, value=value, description=description))
    # unsafe_ask() lets Ctrl+C through as KeyboardInterrupt; ask() would print
    # its own message
    try:
        return questionary.select(message, choices=options, default=default).unsafe_ask()
    except KeyboardInterrupt:
        return None


def pick_inputs(selected):
    return inputs.pick_inputs(selected, ask, inputs.choose_path, inputs.path_problem, show)


def pick_dates(exam_calendar, mode):
    return calendars.choose_dates(exam_calendar, mode)


def confirm(question, detail):
    """A yes/no question, after the detail it is about. Ctrl+C counts as no."""
    show(detail)
    try:
        return questionary.confirm(question).unsafe_ask()
    except KeyboardInterrupt:
        return False


def choose(question, options):
    """A menu of plain options. Returns the chosen option's index; Ctrl+C
    picks the last option, which is always the way back or out."""
    choices = []
    for index, option in enumerate(options):
        choices.append((option, index, None))
    answer = ask(question, choices)
    if answer is None:
        return len(options) - 1
    return answer


def show(text):
    print(text, flush=True)


def pause(text):
    """Show a message and wait, so it can be read before the next menu."""
    show(text)
    try:
        input("Press Enter to go back and change your choices...")
    except KeyboardInterrupt:
        pass
