"""Start the exam planner app:

    python app.py

Run it in a terminal window (PowerShell or Windows Terminal on Windows, the
normal terminal on Linux and Mac), not with its input or output redirected.
"""

import sys


def main():
    # the arrow-key menus need a real terminal window to read keys from
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Run the app in an interactive terminal window: PowerShell, Command Prompt or "
              "Windows Terminal on Windows, the normal terminal on Linux and Mac.")
        return 1

    try:
        import tkinter

        import flow
        import planner
        import terminal
    except ImportError as error:
        print(f"A Python package the app needs is missing: {error}")
        print("Set up the app as README.md says, then try again.")
        return 1

    try:
        flow.run_workflow(terminal, planner)
    except EOFError:
        print("The terminal input closed.")
    except KeyboardInterrupt:
        print("Stopped.")
    except (OSError, RuntimeError, tkinter.TclError) as error:
        print(f"Could not go on: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
