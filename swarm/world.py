"""The lattice and the target structures units assemble into.

Units live on a 2D integer lattice (a Robrick unit occupies one cell). A target
structure is just a frozen set of cells; the assembly algorithm is agnostic to
which one it's building. Coordinates are (x, y) with y increasing upward, so a
staircase literally steps up to the right.
"""
from __future__ import annotations

from typing import Iterable

Cell = tuple[int, int]

# Four-connected lattice: a Robrick unit bonds to its orthogonal neighbours.
_OFFSETS: tuple[Cell, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def neighbours(cell: Cell) -> list[Cell]:
    """The four lattice neighbours of `cell`."""
    x, y = cell
    return [(x + dx, y + dy) for dx, dy in _OFFSETS]


def staircase(steps: int = 4, tread: int = 2, riser: int = 1) -> frozenset[Cell]:
    """A staircase: `steps` treads, each `tread` cells deep, rising `riser` per step.

    Step k occupies the rectangle [k*tread, (k+1)*tread) in x and [0, (k+1)*riser)
    in y — a solid filled staircase a Repairer Bot could climb. The seed sits at
    the bottom-left, the natural anchor for gradient growth.
    """
    cells: set[Cell] = set()
    for k in range(steps):
        x0 = k * tread
        height = (k + 1) * riser
        for x in range(x0, x0 + tread):
            for y in range(height):
                cells.add((x, y))
    return frozenset(cells)


def ramp(length: int = 6, height: int = 4) -> frozenset[Cell]:
    """A solid right triangle ramp of the given footprint."""
    cells: set[Cell] = set()
    for x in range(length):
        col_height = 1 + round((height - 1) * x / max(1, length - 1))
        for y in range(col_height):
            cells.add((x, y))
    return frozenset(cells)


def bridge(span: int = 8, deck: int = 2, pier_height: int = 3) -> frozenset[Cell]:
    """A flat deck on two end piers — a structure that must stay connected to build."""
    cells: set[Cell] = set()
    # piers
    for y in range(pier_height):
        for x in range(deck):
            cells.add((x, y))
            cells.add((span - 1 - x, y))
    # deck
    for x in range(span):
        for y in range(pier_height, pier_height + deck):
            cells.add((x, y))
    return frozenset(cells)


def anchor_of(shape: Iterable[Cell]) -> Cell:
    """The seed cell: bottom-most, then left-most. The gradient grows from here."""
    return min(shape, key=lambda c: (c[1], c[0]))
