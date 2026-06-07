"""Run the self-assembly simulator from the command line.

    swarm-assemble run  --shape staircase           # assemble and show it grow
    swarm-assemble heal --shape staircase --damage 6 # assemble, damage, self-heal
"""
from __future__ import annotations

import argparse

from swarm.assembly import SelfAssembly
from swarm.world import bridge, ramp, staircase

_SHAPES = {"staircase": staircase, "ramp": ramp, "bridge": bridge}


def _build(name: str):
    return _SHAPES[name]()


def _cmd_run(args: argparse.Namespace) -> int:
    sim = SelfAssembly(_build(args.shape))
    print(f"shape={args.shape}  units={len(sim.shape)}  seed={sim.seed}")
    print(f"distributed gradient converged in {sim.gradient_rounds} rounds")
    result = sim.run()
    print(f"assembled in {result.rounds} rounds  "
          f"({result.settled}/{result.target}, {result.completion:.0%} complete)")
    print(f"units settled per round: {result.per_round_new}")
    print(sim.render())
    return 0


def _cmd_heal(args: argparse.Namespace) -> int:
    sim = SelfAssembly(_build(args.shape))
    sim.run()
    # deterministically damage the N highest-gradient (outermost) units
    victims = sorted(
        (c for c in sim.settled if c != sim.seed),
        key=lambda c: -sim.gradient[c],
    )[: args.damage]
    sim.remove(victims)
    print(f"damaged {len(victims)} units; structure now "
          f"{len(sim.settled)}/{len(sim.shape)}")
    print(sim.render())
    recovery = sim.run()
    print(f"\nself-healed in {recovery.rounds} rounds -> "
          f"{recovery.settled}/{recovery.target} ({recovery.completion:.0%})")
    print(sim.render())
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="swarm-assemble")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="assemble a shape")
    pr.add_argument("--shape", choices=_SHAPES, default="staircase")
    pr.set_defaults(func=_cmd_run)

    ph = sub.add_parser("heal", help="assemble, damage, then self-heal")
    ph.add_argument("--shape", choices=_SHAPES, default="staircase")
    ph.add_argument("--damage", type=int, default=6)
    ph.set_defaults(func=_cmd_heal)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
