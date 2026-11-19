"""Start the menu with the clearer 'Who teaches what' label.

This separate launcher preserves existing files, as requested by Krish.
Only the in-memory display label changes; the teaching input stays the same.
"""

from dataclasses import replace
import sys

import menu


def main():
    original_inputs = menu.INPUTS
    menu.INPUTS = tuple(
        replace(item, label="Who teaches what") if item.key == "teaching" else item
        for item in original_inputs
    )
    try:
        return menu.main()
    finally:
        menu.INPUTS = original_inputs


if __name__ == "__main__":
    sys.exit(main())
