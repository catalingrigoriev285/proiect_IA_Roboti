"""Entry-point CLI pentru nav_robot.

Subcomenzi disponibile:
    generate     - genereaza o harta aleatoare seed-based si optional o salveaza/afiseaza.
    build-scene  - construieste obstacolele din harta in scena CoppeliaSim deschisa.

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


def _cmd_build_scene(args: argparse.Namespace) -> int:
    if args.map:
        grid = GridMap.load(args.map)
        print(f"[..] Harta incarcata din {args.map} (seed={grid.seed}).")
    else:
        grid = generate_random_map(
            width=args.width, height=args.height,
            obstacle_ratio=args.obstacles, seed=args.seed,
        )
        print(f"[..] Harta generata in memorie (seed={args.seed}).")

    from nav_robot.coppelia.client import connect
    from nav_robot.coppelia.scene_builder import (
        build_obstacles_from_map, clear_obstacles_by_alias, place_robot_at_start,
    )

    print(f"[..] Conectare la CoppeliaSim ...")
    _, sim = connect()
    print(f"[OK] Conectat.")

    if args.clear_only:
        n = clear_obstacles_by_alias(sim)
        print(f"[OK] Sterse {n} obiecte din ierarhia 'MapObstacles'.")
        return 0

    parent, handles = build_obstacles_from_map(
        sim, grid, height_m=args.obstacle_height,
    )
    print(f"[OK] Plasati {len(handles)} cuboizi sub dummy-ul 'MapObstacles' (handle={parent}).")

    if args.place_robot:
        try:
            place_robot_at_start(sim, grid)
            print(f"[OK] Robot mutat in start={grid.start} world={grid.to_world(grid.start)}.")
        except Exception as e:
            print(f"[WARN] Nu am putut muta robotul: {e}")

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

    # --- build-scene ---
    p_bs = sub.add_parser(
        "build-scene",
        help="Construieste obstacolele din harta in scena CoppeliaSim deschisa.",
    )
    p_bs.add_argument("--map", type=str, default=None,
                      help="Cale JSON de harta. Daca lipseste, genereaza una nou cu --seed.")
    p_bs.add_argument("--seed", type=int, default=DEFAULT_SEED,
                      help="Seed pentru generare in memorie (folosit doar daca --map lipseste).")
    p_bs.add_argument("--width", type=int, default=DEFAULT_GRID_W)
    p_bs.add_argument("--height", type=int, default=DEFAULT_GRID_H)
    p_bs.add_argument("--obstacles", type=float, default=DEFAULT_OBSTACLE_RATIO)
    p_bs.add_argument("--obstacle-height", type=float, default=0.5,
                      help="Inaltimea cuboizilor in metri (default 0.5).")
    p_bs.add_argument("--place-robot", action="store_true",
                      help="Muta robotul Pioneer in celula start a hartii.")
    p_bs.add_argument("--clear-only", action="store_true",
                      help="Sterge obstacolele anterioare fara sa creeze altele noi.")
    p_bs.set_defaults(func=_cmd_build_scene)

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
