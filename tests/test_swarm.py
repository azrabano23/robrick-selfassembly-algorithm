"""Correctness of the distributed gradient, the assembly rule, and self-healing."""
from collections import deque

from swarm.assembly import SelfAssembly
from swarm.gradient import distributed_gradient
from swarm.world import anchor_of, bridge, neighbours, ramp, staircase


def _bfs(shape, seed):
    """Reference shortest-path field to check the distributed gradient against."""
    dist = {seed: 0}
    q = deque([seed])
    while q:
        c = q.popleft()
        for n in neighbours(c):
            if n in shape and n not in dist:
                dist[n] = dist[c] + 1
                q.append(n)
    return dist


def test_distributed_gradient_equals_bfs():
    for build in (staircase, ramp, bridge):
        shape = build()
        seed = anchor_of(shape)
        field, _ = distributed_gradient(shape, seed)
        assert field == _bfs(shape, seed)


def test_assembly_completes_every_shape():
    for build in (staircase, ramp, bridge):
        sim = SelfAssembly(build())
        result = sim.run()
        assert result.complete
        assert sim.settled == set(sim.shape)


def test_growth_is_gradient_ordered():
    # a unit must never settle before a lower-gradient shape-neighbour of it.
    sim = SelfAssembly(staircase(steps=5))
    settle_round: dict = {sim.seed: 0}
    r = 0
    while sim.settled != set(sim.shape):
        r += 1
        before = set(sim.settled)
        sim.step()
        for c in sim.settled - before:
            settle_round[c] = r
    for c in sim.shape:
        for n in neighbours(c):
            if n in sim.shape and sim.gradient[n] < sim.gradient[c]:
                assert settle_round[n] <= settle_round[c]


def test_self_heals_after_damage():
    sim = SelfAssembly(staircase(steps=4))
    sim.run()
    assert sim.settled == set(sim.shape)
    # remove the 8 outermost units
    victims = sorted((c for c in sim.settled if c != sim.seed),
                     key=lambda c: -sim.gradient[c])[:8]
    sim.remove(victims)
    assert sim.settled != set(sim.shape)
    recovery = sim.run()
    assert recovery.complete
    assert sim.settled == set(sim.shape)


def test_seed_is_indestructible():
    sim = SelfAssembly(ramp())
    sim.run()
    sim.remove([sim.seed])
    assert sim.seed in sim.settled


def test_deterministic():
    a = SelfAssembly(bridge()).run()
    b = SelfAssembly(bridge()).run()
    assert a.per_round_new == b.per_round_new
    assert a.rounds == b.rounds
