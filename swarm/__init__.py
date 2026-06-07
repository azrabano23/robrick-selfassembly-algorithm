"""robrick.swarm — a decentralized self-assembly simulator.

A collective of identical units self-organizes into a target structure (a
staircase, ramp, or bridge) using only *local* rules: each unit talks to its
lattice neighbours, computes a distributed gradient from a seed, and settles
into the structure in gradient order. There is no central controller, no global
map, and no per-unit blueprint — the shape is an emergent property of the local
rule. Remove units mid-run and the same rule heals the holes.

This is a lattice/cellular abstraction of gradient-based swarm assembly
(Rubenstein et al., "Programmable self-assembly in a thousand-robot swarm",
Science 2014). It models the *coordination logic* — distributed gradient,
gradient-ordered growth, self-healing — not the continuous-space locomotion or
edge-following kinematics of physical robots. See the README for that boundary.
"""
from swarm.world import (
    Cell,
    neighbours,
    staircase,
    ramp,
    bridge,
)
from swarm.gradient import distributed_gradient
from swarm.assembly import SelfAssembly, AssemblyResult

__version__ = "0.1.0"

__all__ = [
    "Cell",
    "neighbours",
    "staircase",
    "ramp",
    "bridge",
    "distributed_gradient",
    "SelfAssembly",
    "AssemblyResult",
]
