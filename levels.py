"""Level data, validation, par and ordering.

Each level is 6 strings of 6 characters: '.' is empty, 'R' is the red car,
every other capital letter is one car. "par" is the length of the shortest
solution; it is written down here and re-checked by the BFS solver at start-up.
"""

import string
import time

from rules import EXIT_ROW, HORIZONTAL, RED, SIZE, load_level
from solver import solve

LEVELS = [
    {"name": "Warm-up", "par": 5, "rows": [
        "FFFGG.",
        "ICCHH.",
        "IRR.E.",
        ".B..EA",
        ".B.DDA",
        "......",
    ]},
    {"name": "First jam", "par": 8, "rows": [
        "..A...",
        "..A.BB",
        "RRA...",
        ".CC.D.",
        "....D.",
        "......",
    ]},
    {"name": "Rush hour", "par": 37, "rows": [
        "JJJ.DD",
        ".HHG..",
        "RRBG..",
        "..B.CC",
        "FAA.I.",
        "FEE.I.",
    ]},
    {"name": "Side street", "par": 11, "rows": [
        "EE..HH",
        "..GG.D",
        "RR.FAD",
        "I..FAJ",
        "IBBB.J",
        "I.CC.J",
    ]},
    {"name": "Crossroads", "par": 17, "rows": [
        "K.HHII",
        "KCCE.J",
        ".RRE.J",
        "DD.EF.",
        ".GAAF.",
        ".G.BB.",
    ]},
    {"name": "Twin trucks", "par": 23, "rows": [
        "...AC.",
        "...AC.",
        "RR.GBH",
        "...GBH",
        ".F.EED",
        ".F...D",
    ]},
    {"name": "Gridlock", "par": 29, "rows": [
        ".D.BJJ",
        ".D.BC.",
        "RR..CA",
        "HHFFCA",
        "KGG.II",
        "K.LLEE",
    ]},
]

ALLOWED = set(string.ascii_uppercase) | {"."}


def check_level(rows):
    """Return (cars, state) for a well-formed level or raise ValueError(reason)."""
    if not isinstance(rows, (list, tuple)) or len(rows) != SIZE:
        raise ValueError(f"needs {SIZE} rows")
    for r, line in enumerate(rows):
        if not isinstance(line, str) or len(line) != SIZE:
            raise ValueError(f"row {r} must be {SIZE} characters")
        bad = set(line) - ALLOWED
        if bad:
            raise ValueError(f"row {r} has invalid character(s) {''.join(sorted(bad))!r}")
    cars, state = load_level(rows)        # raises on bent / wrong-length cars
    if RED not in cars:
        raise ValueError("there is no red car R")
    red_row, _ = state[sorted(cars).index(RED)]
    if cars[RED].orient != HORIZONTAL or red_row != EXIT_ROW:
        raise ValueError(f"red car must lie across on row {EXIT_ROW}")
    return cars, state


def prepare_levels(levels=LEVELS, report=print):
    """Validate and solve every level; return the good ones sorted by par.

    Each returned dict has: name, rows, cars, start, par, solution.
    Bad levels are reported (which one and why) and skipped.
    """
    ready = []
    for number, level in enumerate(levels, start=1):
        name = level.get("name", f"#{number}")
        try:
            cars, start = check_level(level.get("rows"))
            t0 = time.perf_counter()
            solution = solve(cars, start)
            took = time.perf_counter() - t0
            if solution is None:
                raise ValueError("the solver found no solution")
            if solution == []:
                raise ValueError("it is already solved at the start")
        except ValueError as err:
            report(f"Skipping level {number} ({name}): {err}")
            continue
        par = len(solution)
        if level.get("par") not in (None, par):
            report(f"Level {number} ({name}): stored par {level['par']} "
                   f"corrected to {par}")
        ready.append({"name": name, "rows": level["rows"], "cars": cars,
                      "start": start, "par": par, "solution": solution,
                      "solve_time": took})
    ready.sort(key=lambda lv: lv["par"])
    return ready
