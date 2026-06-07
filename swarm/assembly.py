"""Decentralized self-assembly by gradient-ordered frontier growth.

The whole controller is one local rule. A unit may settle into an empty target
cell `c` only when:

  1. `c` touches the already-assembled structure (you can only bond to the body),
     and
  2. every neighbour of `c` that belongs to the target shape and has a *lower*
     gradient than `c` is already settled.

Rule 2 is the crucial one and it is entirely local — a unit inspects only its
own neighbours. It forces the structure to grow outward from the seed in
gradient order, so units never settle into a spot that strands a lower gradient
cell behind them. No global plan, no leader, no turn-taking: every fillable cell
on the frontier settles simultaneously, which is exactly the parallelism a real
swarm exploits.

Self-healing falls out for free. Knock units out of the assembled body and the
holes they leave have lower-gradient neighbours that are still settled, so the
very same rule marks them fillable again and the swarm regrows them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from swarm.gradient import INF, distributed_gradient
from swarm.world import Cell, anchor_of, neighbours


@dataclass
class AssemblyResult:
    complete: bool
    rounds: int
    settled: int
    target: int
    per_round_new: list[int] = field(default_factory=list)

    @property
    def completion(self) -> float:
        return self.settled / self.target if self.target else 0.0


class SelfAssembly:
    """Simulate a swarm assembling `shape` from a single seed via the local rule."""

    def __init__(self, shape: frozenset[Cell], seed: Cell | None = None):
        self.shape = shape
        self.seed = seed if seed is not None else anchor_of(shape)
        if self.seed not in shape:
            raise ValueError("seed must lie inside the target shape")
        # Each unit knows its own gradient and its neighbours'; we precompute the
        # field with the distributed primitive (see gradient.py).
        self.gradient, self.gradient_rounds = distributed_gradient(shape, self.seed)
        self.settled: set[Cell] = {self.seed}

    # --- the local rule -------------------------------------------------
    def _fillable(self) -> list[Cell]:
        out: list[Cell] = []
        for c in self.shape:
            if c in self.settled:
                continue
            ns = neighbours(c)
            touches = any(n in self.settled for n in ns)
            if not touches:
                continue
            gc = self.gradient[c]
            lower_all_settled = all(
                (n not in self.shape)
                or (self.gradient[n] >= gc)
                or (n in self.settled)
                for n in ns
            )
            if lower_all_settled:
                out.append(c)
        return out

    # --- driving the simulation ----------------------------------------
    def step(self) -> int:
        """Settle every fillable frontier cell this round. Returns count settled."""
        frontier = self._fillable()
        self.settled.update(frontier)
        return len(frontier)

    def run(self, max_rounds: int = 100_000) -> AssemblyResult:
        per_round: list[int] = []
        rounds = 0
        while self.settled != set(self.shape) and rounds < max_rounds:
            rounds += 1
            n = self.step()
            per_round.append(n)
            if n == 0:
                break  # stuck (shouldn't happen for connected shapes)
        return AssemblyResult(
            complete=self.settled == set(self.shape),
            rounds=rounds,
            settled=len(self.settled),
            target=len(self.shape),
            per_round_new=per_round,
        )

    def remove(self, cells: list[Cell]) -> None:
        """Damage the structure (the seed is indestructible — it's the anchor)."""
        for c in cells:
            if c != self.seed:
                self.settled.discard(c)

    # --- rendering ------------------------------------------------------
    def render(self) -> str:
        xs = [c[0] for c in self.shape]
        ys = [c[1] for c in self.shape]
        lines = []
        for y in range(max(ys), min(ys) - 1, -1):
            row = []
            for x in range(min(xs), max(xs) + 1):
                c = (x, y)
                if c == self.seed:
                    row.append("S")
                elif c in self.settled:
                    row.append("#")
                elif c in self.shape:
                    row.append(".")
                else:
                    row.append(" ")
            lines.append("".join(row))
        return "\n".join(lines)
