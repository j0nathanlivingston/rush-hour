"""Game rules for Rush Hour: the only place that knows how cars move.

Data model
----------
cars  : dict  letter -> Car(orient, length)        never changes during a level
state : tuple of (row, col) top-left cells, one per car, in alphabetical
        car order. A tuple (not a list) so it is hashable and can live in a
        set or be a dict key, which the BFS solver relies on.
grid  : 6x6 list of lists; each cell holds the covering car's letter or None.
move  : (letter, step) with step +1 (right/down) or -1 (left/up).
"""

from collections import namedtuple

SIZE = 6          # the board is SIZE x SIZE
RED = "R"         # letter of the red car
EXIT_ROW = 2      # the red car's row; the exit is on the right edge of it
HORIZONTAL = "horizontal"
VERTICAL = "vertical"

Car = namedtuple("Car", ["orient", "length"])


def load_level(rows):
    """Turn 6 strings of 6 chars into (cars, starting state).

    Raises ValueError with a readable reason if a car is not a straight
    line of 2 or 3 cells.
    """
    cells = {}                                   # letter -> list of (r, c)
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch != ".":
                cells.setdefault(ch, []).append((r, c))

    cars = {}
    top_left = {}
    for letter in sorted(cells):
        cs = sorted(cells[letter])               # row-major: first is top-left
        n = len(cs)
        r0, c0 = cs[0]
        if n not in (2, 3):
            raise ValueError(f"car {letter} has {n} cells (must be 2 or 3)")
        if cs == [(r0, c0 + i) for i in range(n)]:
            orient = HORIZONTAL
        elif cs == [(r0 + i, c0) for i in range(n)]:
            orient = VERTICAL
        else:
            raise ValueError(f"car {letter} is not one straight, unbroken line")
        cars[letter] = Car(orient, n)
        top_left[letter] = (r0, c0)

    state = tuple(top_left[letter] for letter in sorted(cars))
    return cars, state


def car_cells(car, pos):
    """All cells covered by a car whose top-left cell is pos."""
    r, c = pos
    if car.orient == HORIZONTAL:
        return [(r, c + i) for i in range(car.length)]
    return [(r + i, c) for i in range(car.length)]


def build_grid(cars, state):
    """6x6 list of lists with the letter of the car covering each cell."""
    grid = [[None] * SIZE for _ in range(SIZE)]
    for letter, pos in zip(sorted(cars), state):
        for r, c in car_cells(cars[letter], pos):
            grid[r][c] = letter
    return grid


def legal_moves(cars, state):
    """Every move of one cell that lands inside the board on an empty cell."""
    grid = build_grid(cars, state)
    moves = []
    for letter, (r, c) in zip(sorted(cars), state):
        car = cars[letter]
        if car.orient == HORIZONTAL:
            behind, ahead = (r, c - 1), (r, c + car.length)
        else:
            behind, ahead = (r - 1, c), (r + car.length, c)
        for step, (tr, tc) in ((-1, behind), (+1, ahead)):
            if 0 <= tr < SIZE and 0 <= tc < SIZE and grid[tr][tc] is None:
                moves.append((letter, step))
    return moves


def apply_move(cars, state, move):
    """Return a NEW state with one car shifted by one cell (old one untouched)."""
    letter, step = move
    i = sorted(cars).index(letter)
    r, c = state[i]
    if cars[letter].orient == HORIZONTAL:
        new_pos = (r, c + step)
    else:
        new_pos = (r + step, c)
    return state[:i] + (new_pos,) + state[i + 1:]


def is_won(cars, state):
    """True when the red car's right end is in the last column."""
    i = sorted(cars).index(RED)
    _, c = state[i]
    return c + cars[RED].length - 1 == SIZE - 1
