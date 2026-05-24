"""Construirea dinamica a scenei CoppeliaSim din GridMap."""

from __future__ import annotations

import logging
import math
import random

import numpy as np

from nav_robot.map.grid_map import OBSTACLE, GridMap

log = logging.getLogger("coppelia.scene")

# Numele dummy-ului parinte sub care se grupeaza toate obstacolele.
# Folosit ca marker pentru a sterge obstacolele anterioare la o noua rulare.
DEFAULT_PARENT_ALIAS = "MapObstacles"


# Liste cu modele din ModelBrowser CoppeliaSim, grupate pe teme. Cale relativa
# la directorul `models/` al instalarii CoppeliaSim. sim.loadModel le accepta.
# Daca un model nu exista in versiunea ta de CoppeliaSim, este sarit silentios.
MODEL_THEMES: dict[str, list[str]] = {
    "mobilier": [
        "models/furniture/chairs/dining chair.ttm",
        "models/furniture/chairs/swivel chair.ttm",
        "models/furniture/chairs/Office chair.ttm",
        "models/furniture/chairs/sofaChair.ttm",
        "models/furniture/tables/customizable table.ttm",
        "models/furniture/tables/diningTable.ttm",
        "models/furniture/plants/indoorPlant.ttm",
        "models/furniture/plants/plant.ttm",
        "models/furniture/shelves/shelf.ttm",
    ],
    "depozit": [
        "models/equipment/storage/cardboard box.ttm",
        "models/equipment/storage/box.ttm",
        "models/equipment/storage/wooden box.ttm",
        "models/equipment/storage/sealed box.ttm",
        "models/equipment/luggage/luggage.ttm",
        "models/equipment/storage/pallet.ttm",
        "models/components/Wooden box (large).ttm",
        "models/components/Wooden box (small).ttm",
    ],
    "strada": [
        "models/infrastructure/walls/80cm high wall section.ttm",
        "models/infrastructure/walls/250cm high wall section.ttm",
        "models/equipment/cones/Traffic cone.ttm",
        "models/equipment/cones/traffic cone.ttm",
        "models/components/Traffic cone.ttm",
        "models/equipment/storage/barrel.ttm",
        "models/equipment/storage/Wooden barrel.ttm",
        "models/nature/trees/Tall tree.ttm",
        "models/nature/trees/tree.ttm",
    ],
    "mixt": [
        "models/furniture/chairs/dining chair.ttm",
        "models/furniture/plants/indoorPlant.ttm",
        "models/equipment/storage/cardboard box.ttm",
        "models/equipment/cones/Traffic cone.ttm",
        "models/equipment/storage/barrel.ttm",
        "models/components/Wooden box (large).ttm",
        "models/nature/trees/Tall tree.ttm",
    ],
}


def list_themes() -> list[str]:
    return list(MODEL_THEMES.keys())


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


def build_realistic_obstacles_from_map(
    sim,
    grid: GridMap,
    theme: str = "mobilier",
    parent_alias: str = DEFAULT_PARENT_ALIAS,
    clear_existing: bool = True,
    with_floor: bool = True,
    floor_margin_m: float = 1.0,
    floor_thickness_m: float = 0.05,
    floor_color: tuple[float, float, float] = (0.85, 0.85, 0.85),
    height_m: float = 0.5,
    fallback_color: tuple[float, float, float] = (0.5, 0.4, 0.3),
    random_rotation: bool = True,
    seed: int = 42,
) -> tuple[int, list[int]]:
    """Construieste o scena REALISTA: pentru fiecare cluster de obstacole pune
    un model 3D ales din ModelBrowser (tema specificata).

    Algoritm:
        1. Identifica clusterele de celule de obstacol (connected components, 8-conn).
        2. Pentru fiecare cluster: calculeaza centroidul si bounding-box-ul.
        3. Incarca un model aleator din tema; daca esueaza, foloseste cuboid.
        4. Plaseaza modelul la centroid, cu rotatie aleatoare (optional).
        5. Pentru celule din cluster care raman descoperite (cluster mare > model),
           adauga cuboizi-fallback semitransparenti ca senzorii sa-i detecteze.

    Args:
        sim: API CoppeliaSim.
        grid: harta sursa.
        theme: una din `list_themes()` - "mobilier", "depozit", "strada", "mixt".
        parent_alias: dummy parent pentru grupare/clear.
        clear_existing: sterge MapObstacles vechi.
        with_floor: adauga floor static.
        floor_*: parametri floor.
        height_m: inaltimea fallback-cuboidului (cand modelul nu se incarca).
        fallback_color: culoare cuboid-fallback.
        random_rotation: orientare aleatoare in jurul Z.
        seed: pentru reproducibilitate.

    Returns:
        (parent_handle, lista_handle-uri create - floor + modele + cuboizi-fallback)
    """
    if clear_existing:
        clear_obstacles_by_alias(sim, parent_alias)

    parent = sim.createDummy(0.05)
    sim.setObjectAlias(parent, parent_alias)
    sim.setObjectPosition(parent, [0.0, 0.0, 0.0], sim.handle_world)

    handles: list[int] = []

    if with_floor:
        world_w, world_h = grid.world_size()
        floor_sx = world_w + 2 * floor_margin_m
        floor_sy = world_h + 2 * floor_margin_m
        floor = _create_static_cuboid(sim, [floor_sx, floor_sy, floor_thickness_m],
                                      floor_color)
        cx, cy = world_w / 2.0, world_h / 2.0
        sim.setObjectPosition(floor, [cx, cy, -floor_thickness_m / 2.0],
                              sim.handle_world)
        sim.setObjectAlias(floor, "MapFloor")
        sim.setObjectParent(floor, parent, True)
        handles.append(floor)

    # Lista de modele candidate + pre-incarcare ca TEMPLATE-uri (off-scene la z=100)
    candidate_paths = MODEL_THEMES.get(theme, MODEL_THEMES["mixt"])
    rng = random.Random(seed)

    templates: list[tuple[str, int]] = []   # (path, handle)
    for path in candidate_paths:
        h = _try_load_model(sim, path)
        if h is not None and h != -1:
            # Mut template-ul sus la z=100 ca sa nu se vada in scena
            try:
                sim.setObjectPosition(h, [-50.0, -50.0, 100.0], sim.handle_world)
            except Exception:
                pass
            templates.append((path, int(h)))

    if not templates:
        log.warning("Niciun model 3D din tema '%s' n-a putut fi incarcat. "
                    "Fallback la cuboizi simpli.", theme)
    else:
        log.info("Tema '%s': %d/%d modele disponibile (template-uri pre-incarcate).",
                 theme, len(templates), len(candidate_paths))

    # Identifica clusterele (connected components 8-connectivity)
    clusters = _label_clusters(grid)
    cs = grid.cell_size
    log.info("Plasez %d clustere de obstacole ...", len(clusters))

    for cluster_id, cells in clusters.items():
        # Centroidul cluster-ului in coordonate world (metri)
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        # Centroid REAL (nu bounding-box) - mai natural cand clusterele sunt L-shaped
        cx_cell = sum(xs) / len(xs) + 0.5
        cy_cell = sum(ys) / len(ys) + 0.5
        wx = cx_cell * cs
        wy = cy_cell * cs
        # Mic jitter ca sa nu fie totul la centrul perfect al cluster-ului
        jitter_x = rng.uniform(-0.15 * cs, 0.15 * cs)
        jitter_y = rng.uniform(-0.15 * cs, 0.15 * cs)
        wx += jitter_x
        wy += jitter_y

        # Cloneaza un template aleator si pune-l la (wx, wy, 0)
        placed_model = False
        if templates:
            tpl_path, tpl_h = rng.choice(templates)
            new_h = _clone_model(sim, tpl_h)
            if new_h is not None and new_h != -1:
                # Mutare ROBUSTA pe coordonata world (gestioneaza si modele
                # cu copii ne-relativi).
                _place_model_world(sim, new_h, [wx, wy, 0.0])
                if random_rotation:
                    yaw = rng.uniform(0, 2 * math.pi)
                    try:
                        sim.setObjectOrientation(new_h, [0.0, 0.0, yaw],
                                                  sim.handle_world)
                    except Exception:
                        pass
                _make_subtree_static_respondable(sim, new_h)
                try:
                    sim.setObjectAlias(new_h, f"Real_{cluster_id}")
                except Exception:
                    pass
                try:
                    sim.setObjectParent(new_h, parent, True)
                except Exception:
                    pass
                handles.append(new_h)
                placed_model = True
                log.debug("Cluster %d: %s la (%.2f, %.2f)",
                          cluster_id, tpl_path.rsplit('/', 1)[-1], wx, wy)

        # Indiferent daca modelul vizual a fost plasat, adaug cuboid REZIDENT
        # invizibil + respondable peste fiecare celula a clusterului. Asta
        # garanteaza coliziunea fizica + detectia cu senzorii ultrasonici,
        # indiferent de mesh-ul complex al modelului 3D.
        for x, y in cells:
            cuboid = _create_static_cuboid(sim, [cs, cs, height_m],
                                            fallback_color)
            wxx, wyy = grid.to_world((x, y))
            sim.setObjectPosition(cuboid, [wxx, wyy, height_m / 2.0],
                                   sim.handle_world)
            sim.setObjectAlias(cuboid, f"Coll_{x}_{y}")
            if placed_model:
                # Ascunde vizual (layer 0); ramane respondable
                try:
                    sim.setObjectInt32Param(
                        cuboid, sim.objintparam_visibility_layer, 0)
                except Exception:
                    pass
            sim.setObjectParent(cuboid, parent, True)
            handles.append(cuboid)

    # Sterge template-urile ramase (au z=100, nu deranjeaza dar le curatam)
    for _, tpl_h in templates:
        try:
            sim.removeObjects([tpl_h])
        except Exception:
            try:
                sim.removeObject(tpl_h)
            except Exception:
                pass

    log.info("Plasate %d clustere -> %d obiecte total (modele + coliziuni + floor).",
             len(clusters), len(handles))
    return parent, handles


def _clone_model(sim, template_handle: int) -> int | None:
    """Cloneaza un model (cu intreaga ierarhie) folosind copyPasteObjects."""
    try:
        # In CoppeliaSim 4.x: copyPasteObjects([handles], options)
        # options bit 0 = include children
        new_handles = sim.copyPasteObjects([template_handle], 1)
        if not new_handles:
            return None
        return int(new_handles[0])
    except Exception as e:
        log.debug("copyPasteObjects esuat pe %d: %s", template_handle, e)
        return None


def _place_model_world(sim, base_handle: int, target_xyz: list[float]) -> None:
    """Muta un model la `target_xyz` (world), gestionand si copiii ne-relativi.

    Strategie:
        1. Citeste pozitia world a bazei.
        2. Calculeaza delta = target - current.
        3. Aplica delta pe baza si pe TOTI descendentii. Daca copiii sunt
           pozitionati relativ la baza, setObjectPosition pe baza ii muta deja;
           mutarea explicita a copiilor in plus s-ar dubla. Pentru a evita,
           folosim setObjectPosition relativ la PARENT (handle 'parent_handle')
           pe baza, ceea ce muta intregul model coerent.
    """
    try:
        # Cea mai compatibila metoda: pune baza in coords world; copiii relativi
        # urmeaza automat.
        sim.setObjectPosition(base_handle, target_xyz, sim.handle_world)
    except Exception as e:
        log.debug("setObjectPosition esuat pe %d: %s", base_handle, e)


def _try_load_model(sim, model_path: str) -> int | None:
    """Incearca sim.loadModel; returneaza handle sau None la esec."""
    try:
        h = sim.loadModel(model_path)
        if h == -1:
            return None
        return int(h)
    except Exception as e:
        log.debug("loadModel(%r) esuat: %s", model_path, e)
        return None


def _label_clusters(grid: GridMap) -> dict[int, list[tuple[int, int]]]:
    """Connected-components labeling (8-conn) pe celulele obstacol."""
    cells = grid.cells
    h, w = cells.shape
    label = np.zeros((h, w), dtype=np.int32)
    cur = 0
    clusters: dict[int, list[tuple[int, int]]] = {}
    for y in range(h):
        for x in range(w):
            if cells[y, x] != OBSTACLE or label[y, x] != 0:
                continue
            cur += 1
            stack = [(x, y)]
            label[y, x] = cur
            members: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                members.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            if cells[ny, nx] == OBSTACLE and label[ny, nx] == 0:
                                label[ny, nx] = cur
                                stack.append((nx, ny))
            clusters[cur] = members
    return clusters


def _make_subtree_static_respondable(sim, root_handle: int) -> None:
    """Itereaza recursiv si seteaza shape-urile ca static + respondable."""
    stack = [root_handle]
    while stack:
        h = stack.pop()
        try:
            sim.setObjectInt32Param(h, sim.shapeintparam_static, 1)
            sim.setObjectInt32Param(h, sim.shapeintparam_respondable, 1)
        except Exception:
            pass
        idx = 0
        while True:
            try:
                ch = sim.getObjectChild(h, idx)
            except Exception:
                break
            if ch == -1:
                break
            stack.append(ch)
            idx += 1


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


def reset_robot_to_start(sim, grid: GridMap, robot_path: str = "/PioneerP3DX",
                         z_m: float = 0.139, restart_sim: bool = True) -> dict:
    """Opreste robotul, opreste simularea, repozitioneaza la `start` si reporneste.

    Necesar intre rulari de algoritmi: daca robotul a derapat sau a ramas blocat,
    apasarea acestui buton il aduce inapoi in pozitia initiala.

    Args:
        sim: API CoppeliaSim.
        grid: harta sursa (foloseste grid.start).
        robot_path: calea ierarhica a robotului.
        z_m: inaltimea pe Z.
        restart_sim: daca True, reporneste simularea dupa repozitionare.

    Returns:
        dict cu cheile: 'was_running' (bool), 'restarted' (bool), 'position' (tuple).
    """
    import time as _time

    was_running = False
    try:
        state = sim.getSimulationState()
        was_running = state != sim.simulation_stopped
    except Exception:
        pass

    # Opreste motoarele inainte de orice
    try:
        left = sim.getObject(f"{robot_path}/leftMotor")
        right = sim.getObject(f"{robot_path}/rightMotor")
        sim.setJointTargetVelocity(left, 0.0)
        sim.setJointTargetVelocity(right, 0.0)
    except Exception:
        pass

    # Opreste simularea ca sa putem repozitiona "curat" (fara fizica activa)
    if was_running:
        try:
            sim.stopSimulation()
        except Exception:
            pass
        # Asteptare pana la stopped
        for _ in range(50):
            try:
                if sim.getSimulationState() == sim.simulation_stopped:
                    break
            except Exception:
                break
            _time.sleep(0.05)

    place_robot_at_start(sim, grid, robot_path=robot_path, z_m=z_m)

    restarted = False
    if restart_sim and was_running:
        try:
            sim.startSimulation()
            restarted = True
        except Exception:
            pass

    sx, sy = grid.to_world(grid.start)
    return {"was_running": was_running, "restarted": restarted,
            "position": (sx, sy, z_m)}


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
