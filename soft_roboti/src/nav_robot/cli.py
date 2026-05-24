"""Entry-point CLI pentru nav_robot.

Subcomenzi disponibile (faza 1):
    generate    - genereaza o harta aleatoare seed-based si optional o salveaza/afiseaza.

Subcomenzi planificate (stub):
    plan        - calculeaza un traseu pe o harta salvata.
    run         - ruleaza simularea CoppeliaSim cu un planner ales.
    compare     - compara mai multi algoritmi pe aceeasi harta.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from nav_robot.config import (
    DEFAULT_GRID_H,
    DEFAULT_GRID_W,
    DEFAULT_OBSTACLE_RATIO,
    DEFAULT_SEED,
    MAPS_DIR,
    OUTPUTS_DIR,
)
from nav_robot.map import GridMap, generate_random_map
from nav_robot.map.visualization import plot_map, save_figure


def _cmd_generate(args: argparse.Namespace) -> int:
    grid = generate_random_map(
        width=args.width,
        height=args.height,
        obstacle_ratio=args.obstacles,
        seed=args.seed,
    )

    save_path = Path(args.save) if args.save else MAPS_DIR / f"m{args.seed}.json"
    saved = grid.save(save_path)
    print(f"[OK] Harta salvata: {saved}")
    print(f"     dim={grid.width}x{grid.height}, "
          f"obstacole={int(grid.cells.sum())} celule, "
          f"start={grid.start}, goal={grid.goal}")

    if args.plot:
        fig, ax = plt.subplots(figsize=(7, 7))
        plot_map(grid, ax=ax)
        png_path = OUTPUTS_DIR / f"map_seed{args.seed}.png"
        out = save_figure(fig, png_path)
        print(f"[OK] Vizualizare salvata: {out}")
        if args.show:
            plt.show()
        plt.close(fig)

    return 0


def _cmd_not_implemented(name: str) -> int:
    print(f"[STUB] Subcomanda '{name}' nu este implementata in faza 1.", file=sys.stderr)
    print("       Va fi disponibila in fazele 2-5 (vezi README.md).", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nav_robot",
        description="Navigare si planificare de traseu pentru Pioneer P3-DX in CoppeliaSim.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- generate ---
    p_gen = sub.add_parser("generate", help="Genereaza o harta aleatoare seed-based.")
    p_gen.add_argument("--seed", type=int, default=DEFAULT_SEED,
                       help=f"Seed pentru RNG (default {DEFAULT_SEED}).")
    p_gen.add_argument("--width", type=int, default=DEFAULT_GRID_W,
                       help=f"Latimea grilei in celule (default {DEFAULT_GRID_W}).")
    p_gen.add_argument("--height", type=int, default=DEFAULT_GRID_H,
                       help=f"Inaltimea grilei in celule (default {DEFAULT_GRID_H}).")
    p_gen.add_argument("--obstacles", type=float, default=DEFAULT_OBSTACLE_RATIO,
                       help=f"Fractiunea de obstacole [0..0.9) (default {DEFAULT_OBSTACLE_RATIO}).")
    p_gen.add_argument("--save", type=str, default=None,
                       help="Cale fisier JSON (default data/maps/m<seed>.json).")
    p_gen.add_argument("--plot", action="store_true",
                       help="Salveaza si o vizualizare PNG in outputs/.")
    p_gen.add_argument("--show", action="store_true",
                       help="Deschide fereastra matplotlib (necesita --plot).")
    p_gen.set_defaults(func=_cmd_generate)

    # --- stub-uri ---
    for name, helptxt in [
        ("plan", "[STUB] Planifica un traseu pe o harta salvata (faza 2)."),
        ("run", "[STUB] Ruleaza simularea CoppeliaSim cu un planner (faza 3)."),
        ("compare", "[STUB] Compara algoritmi de planificare (faza 5)."),
    ]:
        p = sub.add_parser(name, help=helptxt)
        p.set_defaults(func=lambda _a, _n=name: _cmd_not_implemented(_n))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
