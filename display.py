"""The game2dboard window: drawing, mouse and keyboard, buttons, status bar.

This module only keeps track of the session (current level, state, undo
stack, selection, drag). Every rule question is answered by rules.py and
every hint by solver.py.

game2dboard itself only reports mouse presses and key presses. Dragging and
the button row need a little more, so they are attached to the Tk window
that game2dboard creates (board._canvas / board._root).
"""

import tkinter as tk

from game2dboard import Board

from rules import (EXIT_ROW, HORIZONTAL, RED, SIZE, VERTICAL, apply_move,
                   build_grid, is_won, legal_moves)
from solver import solve

CELL_SIZE = 88                      # must match CELL in tools/make_images.py
MARGIN = 22                         # frame around the board, in pixels
FRAME = "#262938"                   # board frame
PANEL = "#1c1e2a"                   # window background / status bar
TEXT = "#f2f2f5"
MUTED = "#9aa0b8"
EXIT_GREEN = "#5ac46e"

# colours for the other cars, in order; each has images in img/
CAR_COLOURS = ["blue", "yellow", "green", "purple", "orange", "teal",
               "pink", "sky", "lime", "silver"]

# arrow key -> (orientation it is valid for, step)
ARROWS = {
    "Left": (HORIZONTAL, -1), "Right": (HORIZONTAL, +1),
    "Up": (VERTICAL, -1), "Down": (VERTICAL, +1),
}
DIRECTION_NAMES = {(HORIZONTAL, -1): "left", (HORIZONTAL, +1): "right",
                   (VERTICAL, -1): "up", (VERTICAL, +1): "down"}
CONTROLS = ("Drag cars with the mouse, or click one and use the arrow keys\n"
            "H hint · U undo · R restart · N next · Q quit")


class Game:
    def __init__(self, levels, start_message=""):
        self.levels = levels                # already validated, sorted by par
        self.board = Board(SIZE, SIZE)
        self.board.title = "Rush Hour"
        self.board.cell_size = CELL_SIZE
        self.board.cell_spacing = 0         # slot images draw their own gaps
        self.board.margin = MARGIN
        self.board.margin_color = FRAME
        self.board.grid_color = FRAME
        self.board.cell_color = FRAME
        self.board.create_output(background_color=PANEL, color=TEXT, font_size=13)
        self.board.on_start = self.on_start
        self.board.on_mouse_click = self.on_click
        self.board.on_key_press = self.on_key
        self.start_message = start_message
        self.index = 0
        self.finished = False               # True on the end screen
        self.total_moves = 0                # summed over solved levels
        self.drag = None                    # (letter, grab offset) while dragging
        self._build_extras()

    def _build_extras(self):
        """Button row, wrapped status text and mouse-drag events."""
        root = self.board._root
        root.configure(bg=PANEL)
        width = SIZE * CELL_SIZE + 2 * MARGIN
        try:
            self.board._msgbar._label.configure(wraplength=width - 16, justify="center",
                                                pady=6)
        except Exception:
            pass                            # other game2dboard version: no wrap

        bar = tk.Frame(root, bg=PANEL, pady=8)
        bar.pack(side=tk.BOTTOM, fill=tk.X)   # sits just above the status bar
        buttons = [("Hint", "#f0a020", self.press_hint),
                   ("Undo", "#3c7be0", self.press_undo),
                   ("Restart", "#e0414b", self.press_restart),
                   ("Next level", "#4caf63", self.press_next)]
        for text, colour, action in buttons:
            b = tk.Label(bar, text=text, bg=colour, fg="white", cursor="hand2",
                         font=(None, 13, "bold"), padx=14, pady=7)
            b.pack(side=tk.LEFT, expand=True, padx=6)
            b.bind("<Button-1>", lambda e, a=action: a())

        canvas = self.board._canvas
        canvas.bind("<B1-Motion>", self.on_drag, add="+")
        canvas.bind("<ButtonRelease-1>", self.on_release, add="+")

    def _draw_exit_notch(self):
        """Open the frame on the right of the red car's row."""
        canvas = self.board._canvas
        x = MARGIN + SIZE * CELL_SIZE
        y = MARGIN + EXIT_ROW * CELL_SIZE
        canvas.create_rectangle(x, y + 6, x + MARGIN, y + CELL_SIZE - 6,
                                fill="#3a3e52", width=0)
        canvas.create_rectangle(x + MARGIN - 5, y + 6, x + MARGIN, y + CELL_SIZE - 6,
                                fill=EXIT_GREEN, width=0)

    # ---------------------------------------------------------------- session
    def run(self):
        self.board.show()

    def on_start(self):
        self._draw_exit_notch()
        self.load(0)
        if self.start_message:
            self.message = self.start_message
            self.draw()

    def load(self, index):
        """Start (or restart) level number `index`."""
        self.index = index
        level = self.levels[index]
        self.cars = level["cars"]
        self.state = level["start"]
        self.par = level["par"]
        self.moves = 0
        self.undo_stack = []                # states before each move
        self.selected = None
        self.drag = None
        self.won = False
        self.finished = False
        others = [letter for letter in sorted(self.cars) if letter != RED]
        self.colour = {letter: CAR_COLOURS[i % len(CAR_COLOURS)]
                       for i, letter in enumerate(others)}
        self.colour[RED] = "red"
        self.message = f"{level['name']}: get the red car to the exit on the right."
        self.draw()

    def name(self, letter):
        return f"the {self.colour[letter]} {'car' if self.cars[letter].length == 2 else 'truck'}"

    def do_move(self, move):
        """Apply a legal move: push undo, count it, check for a win."""
        self.undo_stack.append(self.state)
        self.state = apply_move(self.cars, self.state, move)
        self.moves += 1
        if is_won(self.cars, self.state):
            self.won = True
            self.selected = None
            self.drag = None
            self.total_moves += self.moves
            last = self.index == len(self.levels) - 1
            verdict = "Perfect! " if self.moves == self.par else ""
            self.message = (f"Solved in {self.moves} moves (par {self.par}). {verdict}"
                            f"Press Next {'to finish' if last else 'level'}.")

    # ----------------------------------------------------------------- mouse
    def on_click(self, button, row, col):
        """Mouse press on a cell: select the car there and start a drag."""
        if self.finished:
            return
        letter = build_grid(self.cars, self.state)[row][col]
        if letter is None or self.won:
            self.selected = None
            self.drag = None
            if not self.won:
                self.message = ""
        else:
            self.selected = letter
            r, c = self.state[sorted(self.cars).index(letter)]
            grab = col - c if self.cars[letter].orient == HORIZONTAL else row - r
            self.drag = (letter, grab)
            self.message = f"Selected {self.name(letter)}."
        self.draw()

    def on_drag(self, event):
        """Mouse moved with the button down: slide the car cell by cell."""
        if self.drag is None or self.won or self.finished:
            return
        letter, grab = self.drag
        car = self.cars[letter]
        pixel = event.x if car.orient == HORIZONTAL else event.y
        cell = min(max((pixel - MARGIN) // CELL_SIZE, 0), SIZE - 1)
        target = min(max(cell - grab, 0), SIZE - car.length)   # wanted start cell
        moved = blocked = False
        while not self.won:
            r, c = self.state[sorted(self.cars).index(letter)]
            start = c if car.orient == HORIZONTAL else r
            if start == target:
                break
            move = (letter, 1 if target > start else -1)
            if move not in legal_moves(self.cars, self.state):
                blocked = True
                break
            self.do_move(move)
            moved = True
        if not self.won:
            if blocked:
                self.message = "Blocked"
            elif moved:
                self.message = ""
        self.draw()

    def on_release(self, event):
        self.drag = None

    # ------------------------------------------------------------- keyboard
    def on_key(self, key):
        k = key.lower()
        if k in ("q", "escape"):
            self.board.close()
        elif key in ARROWS:
            if not self.finished:
                self.arrow(key)
                self.draw()
        elif k == "h":
            self.press_hint()
        elif k in ("u", "backspace", "z"):
            self.press_undo()
        elif k == "r":
            self.press_restart()
        elif k == "n":
            self.press_next()

    def arrow(self, key):
        if self.won:
            return
        if self.selected is None:
            self.message = "Select a car first"
            return
        orient, step = ARROWS[key]
        if self.cars[self.selected].orient != orient:
            return                                  # wrong axis: ignore
        move = (self.selected, step)
        if move not in legal_moves(self.cars, self.state):
            self.message = "Blocked"
            return
        self.message = ""
        self.do_move(move)

    # -------------------------------------------- actions (keys and buttons)
    def press_hint(self):
        if self.finished or self.won:
            return
        solution = solve(self.cars, self.state)
        if not solution:
            self.message = "No solution from here - try Undo or Restart"
        else:
            letter, step = solution[0]
            direction = DIRECTION_NAMES[(self.cars[letter].orient, step)]
            self.selected = letter
            self.do_move((letter, step))
            if not self.won:
                self.message = (f"Hint: moved {self.name(letter)} {direction}. "
                                f"{len(solution) - 1} moves to go at best.")
        self.draw()

    def press_undo(self):
        if self.finished or self.won:
            return
        if not self.undo_stack:
            self.message = "Nothing to undo"
        else:
            self.state = self.undo_stack.pop()
            self.moves -= 1
            self.message = "Undone."
        self.draw()

    def press_restart(self):
        if self.finished:
            self.total_moves = 0
            self.load(0)
            return
        self.load(self.index)
        self.message = "Restarted."
        self.draw()

    def press_next(self):
        if self.finished:
            self.total_moves = 0
            self.load(0)
        elif self.index + 1 < len(self.levels):
            self.load(self.index + 1)
        else:
            self.end_screen()

    # --------------------------------------------------------------- drawing
    def end_screen(self):
        self.finished = True
        self.drag = None
        total_par = sum(lv["par"] for lv in self.levels)
        self.board.fill("slot")
        for c in range(SIZE):
            self.board[1][c] = "★"
            self.board[4][c] = "★"
        for c, word in enumerate(["ALL", "LEVELS", "DONE"], start=1):
            self.board[2][c] = word
        self.board[3][2] = "WELL"
        self.board[3][3] = "PLAYED"
        self.board.print(
            f"All {len(self.levels)} levels complete!  Moves on solved levels: "
            f"{self.total_moves}  (par total {total_par})\n"
            f"Press Next level to play again, or Q to quit.")

    def draw(self):
        if self.finished:
            return
        grid = build_grid(self.cars, self.state)
        positions = dict(zip(sorted(self.cars), self.state))
        for r in range(SIZE):
            for c in range(SIZE):
                letter = grid[r][c]
                if letter is None:
                    value = "exit" if (r, c) == (EXIT_ROW, SIZE - 1) else "slot"
                else:
                    car = self.cars[letter]
                    top, left = positions[letter]
                    part = c - left if car.orient == HORIZONTAL else r - top
                    o = "h" if car.orient == HORIZONTAL else "v"
                    # e.g. img/blue-v3-1.png, img/red-h2-0-sel.png
                    value = f"{self.colour[letter]}-{o}{car.length}-{part}"
                    if letter == self.selected:
                        value += "-sel"
                self.board[r][c] = value
        level = self.levels[self.index]
        status = (f"Level {self.index + 1} of {len(self.levels)}  ·  {level['name']}"
                  f"      Moves {self.moves}   ·   Par {self.par}")
        if self.won:
            status += "   ✔"
        self.board.print(f"{status}\n{self.message or ' '}\n{CONTROLS}")
