# Robrick — decentralized swarm self-assembly

[![tests](https://github.com/azrabano23/robrick-selfassembly-algorithm/actions/workflows/tests.yml/badge.svg)](https://github.com/azrabano23/robrick-selfassembly-algorithm/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A swarm of identical robots builds a **staircase out of themselves** — with no boss robot, no global map, and no blueprint. Each unit only talks to its neighbours and follows one local rule, yet the whole structure emerges, and **heals itself** when units are knocked out. This repo is a runnable, tested simulation of that algorithm.

> The 2nd-grade version: little robots on the Moon need to make a staircase so a bigger repair robot can climb up. Nobody's in charge. Each little robot just looks at the robots next to it and decides whether to lock into place. Together they build the whole staircase — and if some get destroyed, the rest rebuild the gap.

Built for **Team 11 — Lunar & Planetary Servicing Swarm Robotics** (Rutgers, CS7–CS9 self-assembly subteam). Author: **Azra Bano**.

---

## The problem

For lunar and planetary servicing you can't ship a single large, rigid robot for every job, and you can't rely on a constant uplink to micromanage a fleet. You want many cheap, identical units that **reconfigure themselves** into whatever structure the task needs — a ramp, a staircase, a bridge — and keep working when some fail. That rules out any central controller. The coordination has to be *decentralized*: every unit runs the same program, sees only its neighbours, and the global structure has to be an *emergent* consequence of that local program.

The two precedents this is modelled on:
- **Fire-ant bridges** — ants assemble living structures from local load-sensing and neighbour density, with no leader.
- **Kilobot S-DASH** (Rubenstein et al., *Science* 2014, "Programmable self-assembly in a thousand-robot swarm") — a thousand robots form arbitrary 2D shapes using gradient formation, localization, and edge-following, and self-repair when robots are removed.

## The algorithm

Three local primitives, no global state:

1. **Distributed gradient** (`swarm/gradient.py`). The seed unit holds `0`; every other unit repeatedly sets its value to `1 + min(neighbour values)`. Run synchronously, this converges to each unit's hop-distance from the seed *through the structure* — a shortest-path field computed without any unit ever seeing past its immediate neighbours. The gradient is the swarm's sense of "how far along the shape am I."

2. **Gradient-ordered frontier growth** (`swarm/assembly.py`). A unit may settle into an empty target cell only when **(a)** that cell touches the assembled body, and **(b)** every lower-gradient shape-neighbour of that cell is already settled. Rule (b) is the whole trick, and it is purely local — a unit inspects only its own neighbours. It forces growth outward from the seed in gradient order, so no unit ever settles into a spot that strands a lower cell behind it. Every fillable cell on the frontier settles in the same round, which is the parallelism a real swarm exploits.

3. **Self-healing**, for free. Knock units out of the body and the holes they leave have lower-gradient neighbours that are still settled — so the *same* rule immediately marks them fillable and the swarm regrows them. No special repair mode; healing is just assembly resumed.

## Results

`swarm-assemble run --shape staircase` (20 units, seed at the bottom-left corner):

```
shape=staircase  units=20  seed=(0, 0)
distributed gradient converged in 11 rounds
assembled in 10 rounds  (20/20, 100% complete)
units settled per round: [1, 1, 2, 2, 2, 3, 3, 2, 2, 1]
      ##
    ####
  ######
S#######
```

The "units settled per round" curve shows the swarm working in parallel — up to 3 units locking in simultaneously once the frontier widens. `swarm-assemble heal --shape staircase --damage 6` knocks out the six outermost units and lets the same rule rebuild them:

```
damaged 6 units; structure now 14/20          self-healed in 4 rounds -> 20/20 (100%)
      ..                                             ##
    ##..                                           ####
  ####..                                         ######
S#######                                         S#######
```

The simulator builds staircases, ramps, and bridges from the same rule (the shape is just a set of cells; the algorithm is shape-agnostic).

## Reproducibility

Pure standard library, fully deterministic. `pytest -q` runs 6 tests that pin the correctness claims:
- the distributed gradient equals a reference BFS field on every shape (so the local update really does compute shortest paths);
- assembly completes every shape (staircase / ramp / bridge);
- **growth is provably gradient-ordered** — no unit settles before a lower-gradient neighbour, checked exhaustively;
- the structure self-heals to 100% after damage;
- the seed is indestructible; and runs are deterministic.

```bash
pip install -e ".[dev]"
swarm-assemble run  --shape staircase
swarm-assemble heal --shape bridge --damage 8
pytest -q
```

## What this is and isn't

This is a **lattice/cellular model of the coordination logic** — distributed gradient, gradient-ordered growth, self-healing. It is deliberately *not* a physics simulation: units occupy grid cells and "move" by settling, so it does not model continuous-space locomotion, the edge-following kinematics real Kilobots use to circulate around the structure, collision avoidance, sensor noise, or the mechanics of load-bearing bonds. Those are the next layer. What the model does faithfully capture — and test — is the part that makes swarm assembly *work*: that a correct global structure, and its repair, can emerge from a single neighbour-only rule with no central controller. Next steps: an edge-following locomotion layer, asynchronous/noisy updates, and a structural-load check so "staircase" means load-bearing, not just shape-complete.

## Why it's interesting beyond robotics

This is a clean, testable instance of the question at the heart of multi-agent systems: *what global behaviour can you guarantee from purely local rules, and how robust is it to failure?* The gradient-ordering invariant here is exactly the kind of local constraint that yields a provable global property (correct, gap-free assembly) and graceful degradation (self-healing) — the properties you want from any decentralized collective, robotic or otherwise.

## License

MIT — see [LICENSE](LICENSE). Author: **Azra Bano**.
