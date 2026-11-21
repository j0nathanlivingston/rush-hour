"""Breadth-first search solver for Rush Hour.

Graph: every board state is a node, every legal move an edge to the state it
produces. All edges cost one move, so BFS finds a shortest solution.
Time and space: O(V + E) over the states reached.
"""

from collections import deque

from rules import apply_move, is_won, legal_moves


def solve(cars, state):
    """Shortest list of moves from state to a win, or None if unsolvable."""
    queue = deque([state])          # states still to explore (FIFO)
    seen = {state}                  # states already put in the queue
    parent = {state: None}          # state -> (previous state, move taken)

    while queue:
        current = queue.popleft()
        if is_won(cars, current):
            moves = []
            while parent[current] is not None:      # walk back to the start
                current, move = parent[current]
                moves.append(move)
            moves.reverse()
            return moves
        for move in legal_moves(cars, current):
            nxt = apply_move(cars, current, move)
            if nxt not in seen:                     # mark seen when queued
                seen.add(nxt)
                parent[nxt] = (current, move)
                queue.append(nxt)
    return None
