"""Construirea dinamica a scenei CoppeliaSim din GridMap."""

from __future__ import annotations

from nav_robot.map.grid_map import OBSTACLE, GridMap

# Numele dummy-ului parinte sub care se grupeaza toate obstacolele.
# Folosit ca marker pentru a sterge obstacolele anterioare la o noua rulare.
DEFAULT_PARENT_ALIAS = "MapObstacles"


def build_obstacles_from_map(
    sim,
    grid: GridMap,
    height_m: float = 0.5,
    parent_alias: str = DEFAULT_PARENT_ALIAS,
    color: tuple[float, float, float] = (0.3, 0.3, 0.35),
    clear_existing: bool = True,
    with_floor: bool = True,
    floor_margin_m: float = 1.0,
    floor_thickness_m: float = 0.05,
    floor_color: tuple[float, float, float] = (0.85, 0.85, 0.85),
) -> tuple[int, list[int]]:
    """Plaseaza cate un cuboid in scena pentru fiecare celula obstacol + (optional) un floor.

    Cuboizii sunt grupati sub un dummy comun cu alias-ul `parent_alias` pentru a putea
    fi stersi rapid intre rulari (`clear_existing=True`).

    Args:
        sim: API CoppeliaSim (returnat de client.connect()).
        grid: harta sursa.
        height_m: inaltimea pe Z a cuboizilor.
        parent_alias: numele dummy-ului parinte.
        color: culoarea RGB a cuboizilor (0..1).
        clear_existing: daca True, sterge orice ierarhie anterioara cu acelasi alias.
        with_floor: daca True, creeaza si un floor static dimensionat sa acopere harta.
        floor_margin_m: cati metri in plus pe fiecare parte fata de harta.
        floor_thickness_m: grosimea floor-ului (Z negativ, top la z=0).
        floor_color: culoarea RGB a floor-ului.

    Returns:
        (parent_handle, lista de handle-uri ale obiectelor create - floor + cuboizi)
    """
    if clear_existing:
        clear_obstacles_by_alias(sim, parent_alias)

    parent = sim.createDummy(0.05)
    sim.setObjectAlias(parent, parent_alias)
    sim.setObjectPosition(parent, [0.0, 0.0, 0.0], sim.handle_world)

    cs = grid.cell_size
    handles: list[int] = []

    if with_floor:
        world_w, world_h = grid.world_size()
        floor_sx = world_w + 2 * floor_margin_m
        floor_sy = world_h + 2 * floor_margin_m
        floor = _create_static_cuboid(sim, [floor_sx, floor_sy, floor_thickness_m],
                                      floor_color)
        # Centrat pe mijlocul hartii, cu top-ul la z = 0
        cx, cy = world_w / 2.0, world_h / 2.0
        sim.setObjectPosition(floor, [cx, cy, -floor_thickness_m / 2.0], sim.handle_world)
        sim.setObjectAlias(floor, "MapFloor")
        sim.setObjectParent(floor, parent, True)
        handles.append(floor)

    for y in range(grid.height):
        for x in range(grid.width):
            if grid.cells[y, x] != OBSTACLE:
                continue
            cuboid = _create_static_cuboid(sim, [cs, cs, height_m], color)
            wx, wy = grid.to_world((x, y))
            sim.setObjectPosition(cuboid, [wx, wy, height_m / 2.0], sim.handle_world)
            sim.setObjectAlias(cuboid, f"Obs_{x}_{y}")
            sim.setObjectParent(cuboid, parent, True)
            handles.append(cuboid)

    return parent, handles


def place_robot_at_start(sim, grid: GridMap, robot_path: str = "/PioneerP3DX",
                         z_m: float = 0.139) -> None:
    """Pozitioneaza robotul in centrul celulei `start` din harta.

    Args:
        sim: API CoppeliaSim.
        grid: harta sursa (foloseste grid.start si grid.cell_size).
        robot_path: calea ierarhica a robotului in scena.
        z_m: inaltimea pe Z (139mm = pivotul implicit al Pioneer P3-DX).
    """
    robot = sim.getObject(robot_path)
    sx, sy = grid.to_world(grid.start)
    sim.setObjectPosition(robot, [sx, sy, z_m], sim.handle_world)
    sim.setObjectOrientation(robot, [0.0, 0.0, 0.0], sim.handle_world)


def clear_obstacles_by_alias(sim, parent_alias: str = DEFAULT_PARENT_ALIAS) -> int:
    """Sterge orice dummy + copii cu alias-ul dat. Returneaza numarul de obiecte sterse."""
    try:
        parent = sim.getObject(f"/{parent_alias}")
    except Exception:
        return 0

    # Strange toate handle-urile din ierarhie (copii + parent)
    to_remove = _collect_subtree(sim, parent)
    if to_remove:
        try:
            sim.removeObjects(to_remove)
        except Exception:
            # Fallback: stergere individuala
            for h in to_remove:
                try:
                    sim.removeObject(h)
                except Exception:
                    pass
    return len(to_remove)


# ----------------------------------------------------------------------
# Helpers interne
# ----------------------------------------------------------------------

def _create_static_cuboid(sim, sizes: list[float],
                          color: tuple[float, float, float]) -> int:
    """Creeaza un cuboid static + respondable in scena."""
    # options bitmask: bit0 = backface culling, bit1 = edges, bit2 = smooth shading
    handle = sim.createPrimitiveShape(sim.primitiveshape_cuboid, list(sizes), 0)
    # Static + respondable astfel incat senzorii ultrasonici sa-l detecteze si sa nu cada.
    try:
        sim.setObjectInt32Param(handle, sim.shapeintparam_static, 1)
        sim.setObjectInt32Param(handle, sim.shapeintparam_respondable, 1)
    except Exception:
        pass
    try:
        sim.setShapeColor(handle, None, sim.colorcomponent_ambient_diffuse, list(color))
    except Exception:
        pass
    return handle


def _collect_subtree(sim, root_handle: int) -> list[int]:
    """Returneaza root_handle + toti descendentii (DFS)."""
    handles: list[int] = []
    stack = [root_handle]
    while stack:
        h = stack.pop()
        handles.append(h)
        idx = 0
        while True:
            try:
                child = sim.getObjectChild(h, idx)
            except Exception:
                break
            if child == -1:
                break
            stack.append(child)
            idx += 1
    return handles
