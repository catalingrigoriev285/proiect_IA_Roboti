# soft_roboti - Navigatie autonoma si planificare de traseu

Proiect Python pentru cursul **Inteligenta Artificiala 2025-2026**.
Tema: *Planificarea traseului unui robot mobil: navigatie cu harta vs fara harta in CoppeliaSim*.

Extinde laboratorul [IA-C lab #06](../teme/IA-C%20lab%20%2306.md) (Pioneer P3-DX + ZMQ Remote API)
cu generare de harti aleatoare (seed), planificare globala de traseu si comportamente reactive
fara harta.

## Arhitectura

```
+-----------------------------+        +------------------------------+
|  Python (nav_robot)         |  ZMQ   |  CoppeliaSim (server)        |
|                             |<-----> |                              |
|  - generator harta (seed)   |  TCP   |  - Pioneer P3-DX             |
|  - planificare (A*/Dij/RRT) | :23000 |  - 16 senzori ultrasonici    |
|  - waypoint follower        |        |  - cuboizi (obstacole)       |
|  - reactive (Bug2, wall)    |        |                              |
+-----------------------------+        +------------------------------+
```

Componente:

- **map/** - generator de harta 2D seed-based + vizualizare matplotlib
- **planners/** - A*, Dijkstra, BFS, RRT/RRT* (interfata comuna `PathPlanner`)
- **reactive/** - Bug2, wall-following (navigatie fara harta)
- **coppelia/** - wrapper peste API ZMQ + scene_builder care plaseaza obstacolele
- **controller/** - urmarire waypoint-uri pe tractiune diferentiala

## Instalare

```powershell
cd soft_roboti
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Utilizare

### Generare harta aleatoare (functional in faza 1)

```powershell
python -m nav_robot.cli generate --seed 42 --width 20 --height 20 --obstacles 0.25 --plot
```

Genereaza o harta 20x20 cu 25% obstacole, o salveaza in `data/maps/m42.json`
si produce `outputs/map_seed42.png`. Aceeasi valoare a `--seed` produce mereu aceeasi harta.

### Subcomenzi viitoare (stub-uri in faza 1)

```powershell
python -m nav_robot.cli plan    --map data/maps/m42.json --algo astar
python -m nav_robot.cli run     --map data/maps/m42.json --algo astar
python -m nav_robot.cli compare --map data/maps/m42.json
```

## Status componente

| Modul                       | Status                |
| --------------------------- | --------------------- |
| map/grid_map.py             | functional            |
| map/generator.py            | functional            |
| map/visualization.py        | functional            |
| cli.py (subcomanda generate)| functional            |
| config.py                   | functional            |
| planners/*                  | stub (faza 2)         |
| reactive/*                  | stub (faza 4)         |
| coppelia/*                  | stub (faza 3)         |
| controller/*                | stub (faza 3)         |

## Roadmap

1. **Faza 1 (curenta):** structura + generator harta + vizualizare
2. **Faza 2:** A* + Dijkstra + BFS, comparatie pe aceeasi harta
3. **Faza 3:** integrare CoppeliaSim - scene_builder + waypoint follower
4. **Faza 4:** Bug2 + wall-following (mod fara harta) + script comparatie harta vs fara
5. **Faza 5:** RRT/RRT* + benchmark final

## Testare

```powershell
pip install pytest
pytest tests/
```

## Structura proiect

```
soft_roboti/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- src/nav_robot/
|   |-- cli.py            config.py
|   |-- map/              grid_map.py  generator.py  visualization.py
|   |-- planners/         base.py  astar.py  dijkstra.py  bfs.py  rrt.py
|   |-- reactive/         bug2.py  wall_following.py
|   |-- coppelia/         client.py  robot.py  sensors.py  scene_builder.py
|   |-- controller/       waypoint_follower.py  differential_drive.py
|-- data/maps/
|-- outputs/
|-- scenes/
|-- tests/
```
