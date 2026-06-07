"""Distributed gradient formation.

Every unit holds one integer, its gradient value. The seed holds 0. Every other
unit repeatedly sets its value to `1 + min(neighbour values)`. Run this local
update synchronously across all units and it converges to the hop distance from
the seed *through the structure* — i.e. a shortest-path field computed with no
unit ever seeing more than its immediate neighbours. This is the same primitive
Kilobots use to know "how far along the shape am I", and it is what gives the
assembly its fill order and its ability to self-heal.
"""
from __future__ import annotations

from swarm.world import Cell, neighbours

INF = float("inf")


def distributed_gradient(
    cells: frozenset[Cell], seed: Cell, max_rounds: int = 10_000
) -> tuple[dict[Cell, float], int]:
    """Return (gradient field, rounds-to-converge) over `cells` rooted at `seed`.

    Synchronous local update: value[c] = 0 if c is the seed else 1 + min over
    occupied neighbours. Equivalent to BFS distance, but computed the way a
    swarm computes it — purely from neighbour state, no global view.
    """
    value: dict[Cell, float] = {c: (0.0 if c == seed else INF) for c in cells}
    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        changed = False
        nxt = dict(value)
        for c in cells:
            if c == seed:
                continue
            best = INF
            for n in neighbours(c):
                if n in value and value[n] + 1 < best:
                    best = value[n] + 1
            if best != value[c]:
                nxt[c] = best
                changed = True
        value = nxt
        if not changed:
            break
    return value, rounds
