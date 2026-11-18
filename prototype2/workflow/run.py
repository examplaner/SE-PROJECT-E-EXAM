"""Launch the complete interactive planning workflow."""

import sys


def main():
    try:
        from interface import TerminalUI
        from flow import run_workflow
    except ImportError as error:
        print(f"A required Python component is unavailable: {error}")
        print("Use the existing Anaconda Python with PyYAML and Tkinter, as shown in workflow/README.md.")
        return 1
    import tkinter as tk
    try:
        run_workflow(TerminalUI())
    except EOFError:
        print("Terminal input closed.")
    except KeyboardInterrupt:
        print("Workflow interrupted.")
    except (OSError, RuntimeError, tk.TclError) as error:
        print(f"Could not continue: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
