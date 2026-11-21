"""Rush Hour - start here:  python main.py"""

import sys

from display import Game
from levels import prepare_levels


def main():
    problems = []

    def report(text):
        print(text, file=sys.stderr)
        problems.append(text)

    levels = prepare_levels(report=report)
    if not levels:
        print("No playable levels - fix levels.py", file=sys.stderr)
        sys.exit(1)
    note = ""
    if problems:
        note = f"{len(problems)} level problem(s) reported in the console."
    Game(levels, start_message=note).run()


if __name__ == "__main__":
    main()
