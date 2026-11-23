# Rush Hour

A playable Rush Hour sliding-block puzzle on a 6×6 grid, with a BFS solver
that knows the shortest solution of every level.

## Install and run

Needs Python 3.8+ with Tkinter (included in the python.org installers; on
Debian/Ubuntu: `sudo apt install python3-tk`).

```bash
pip install game2dboard
python main.py
```

## Controls

| Input | Action |
|---|---|
| Drag a car with the mouse | Slides it cell by cell along its own direction until it is blocked (each cell is one move) |
| Mouse click on a car | Select it (yellow outline) |
| Click on an empty cell | Clear the selection |
| Arrow keys | Move the selected car one cell along its own direction |
| H or **Hint** button | Hint: the solver plays the best next move from the current position |
| U (or Backspace) or **Undo** button | Undo the last move |
| R or **Restart** button | Restart the level |
| N or **Next level** button | Next level (after the last level: end screen; there, it plays again) |
| Q / Esc | Quit |

The status bar shows the level, moves made, par, and messages such as
"Blocked", "Select a car first", "Nothing to undo" or
"Solved in 9 moves (par 7)".

## Rules

* Cars are 2 or 3 cells long and lie across (horizontal) or down (vertical).
* A car slides only along its own direction, one cell per move, never
  through another car or off the board.
* The red car **R** sits on row 2 (the third row). Get its right end to the
  **EXIT** on the right edge of that row to win.
* Par is the fewest possible moves, as found by the solver. Every one-cell
  slide counts as one move.

## Stars and skipping

Each solved level earns stars for how much help you needed:

| Hints used on the level | Stars |
|---|---|
| none | ★★★ |
| 1 to 3 | ★★☆ |
| 4 or more | ★☆☆ |
| level skipped (Next pressed before solving) | ☆☆☆ |

Hints count for the whole level, including across restarts: once you have
seen a hint, restarting does not wipe it. If you solve a level twice, the
better result is kept. The status bar shows the hints used on this level,
how many levels are solved and the stars so far (out of 3 per level); the
end screen shows the stars for every level and lists any skipped ones.
Skipped levels never count as solved.

## Files

| File | Holds |
|---|---|
| `main.py` | Starts the game: loads and checks the levels, opens the window |
| `rules.py` | `load_level`, `build_grid`, `legal_moves`, `apply_move`, `is_won` |
| `display.py` | The game2dboard window, drawing, mouse drag/click and key handling, buttons, status bar |
| `solver.py` | `solve` (breadth-first search) |
| `levels.py` | Level strings, validation, par, sorting |
| `img/` | Car pictures cut into one slice per cell, e.g. `blue-v3-1.png` (middle of a vertical blue truck), `red-h2-0-sel.png` (back of the selected red car); plus `slot.png` and `exit.png` |
| `tools/make_images.py` | Regenerates `img/` (needs `pip install pillow`; not needed to play) |

## How the drawing works

game2dboard shows one value per cell, and looks for `img/<value>.png`.
Each car is drawn once as a whole top-down picture (cars are 2 cells,
trucks 3; facing right when horizontal, down when vertical) and cut into
one slice per cell, so `display.draw` just writes the right slice name into
each cell. The red car is always red, with white racing stripes and a glow so it stands out; the other cars get colours in order.

game2dboard only reports mouse presses and key presses, so mouse dragging
and the button row are attached to the Tk window it creates
(`board._canvas`, `board._root`).

## Level format

Six strings of six characters: `.` empty, `R` the red car, any other capital
letter one car. Add a level to `LEVELS` in `levels.py`; its `par` is checked
(and corrected, with a console note) by the solver at start-up.

```
..A...
..A.BB
RRA...
.CC.D.
....D.
......
```

At start-up every level is checked: 6 rows of 6 valid characters, every car
a straight line of 2 or 3 cells, exactly one red car lying across row 2, and
solvable by the solver. A bad level is reported in the console (which level
and why) and skipped; the rest are sorted by par so difficulty rises.

## Where each algorithm and data structure is used

| Data structure / algorithm | Where | Why |
|---|---|---|
| `dict` letter → `Car(orient, length)` | `rules.load_level` → `cars` | Car shapes never change, so they are stored once, apart from positions |
| `tuple` of `(row, col)` in alphabetical car order | the board **state** everywhere | Immutable and hashable, so it can be put in a `set` and used as a `dict` key; `apply_move` returns a new tuple and never changes the old one |
| 6×6 list of lists | `rules.build_grid` | Constant-time "is this cell free?" checks in `legal_moves`, and what `display.draw` paints |
| `(letter, ±1)` pairs | moves | Small, comparable values: `move in legal_moves(...)` checks a key press |
| Graph of states | `solver.solve` | Nodes are states, edges are legal moves, every edge costs 1 |
| Breadth-first search with `collections.deque` (FIFO queue) | `solver.solve` | Explores states in order of distance, so the first won state found is a shortest solution |
| `set` of seen states | `solver.solve` | A state is marked when queued, so it is never queued or explored twice |
| `dict` state → (previous state, move) | `solver.solve` | Walked backwards from the win and reversed to rebuild the move list |
| List used as a stack | `display.Game.undo_stack` | Each move pushes the state before it; Undo pops it (LIFO) |
| Sort by par | `levels.prepare_levels` | Levels are played from easiest to hardest |

BFS runs in O(V + E) time and space over the states reached. The hardest
shipped level (par 37) solves in well under a second, so Hint is instant.
