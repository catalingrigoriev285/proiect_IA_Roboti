# soft_roboti - Navigatie autonoma si planificare de traseu

Proiect Python pentru cursul **Inteligenta Artificiala 2025-2026**.
Tema: *Planificarea traseului unui robot mobil: navigatie cu harta vs fara harta in CoppeliaSim*.

Extinde laboratorul [IA-C lab #06](../teme/IA-C%20lab%20%2306.md) (Pioneer P3-DX + ZMQ Remote API)
cu generare de harti aleatoare seed-based, planificare globala de traseu, comportamente
reactive fara harta si invatare prin recompensa (Q-learning, SARSA, GA).

## Arhitectura

```
+-----------------------------+        +------------------------------+
|  Python (nav_robot)         |  ZMQ   |  CoppeliaSim (server)        |
|                             |<-----> |                              |
|  - generator harta (seed)   |  TCP   |  - Pioneer P3-DX             |
|  - planificare (A*/Dij/RRT) | :23000 |  - 16 senzori ultrasonici    |
|  - reactive (Bug2, wall)    |        |  - cuboizi (obstacole)       |
|  - RL (Q-learning/SARSA/GA) |        |                              |
|  - waypoint follower        |        |                              |
|  - GUI PySide6              |        |                              |
+-----------------------------+        +------------------------------+
```

Componente:

- **map/** - generator de harta 2D seed-based + vizualizare matplotlib
- **planners/** - A*, Dijkstra, BFS, RRT/RRT* (interfata comuna `PathPlanner`)
- **reactive/** - Bug2, wall-following (navigatie fara harta)
- **rl/** - Q-learning, SARSA, algoritm genetic, evaluare si vizualizare politici
- **coppelia/** - wrapper peste API ZMQ + scene_builder care plaseaza obstacolele
- **controller/** - urmarire waypoint-uri pe tractiune diferentiala
- **gui/** - interfata PySide6 cu taburi pentru fiecare etapa (harta / algoritmi / RL / live)

## Instalare

```powershell
cd soft_roboti
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Interfata grafica

```powershell
python -m nav_robot.cli gui
```

Fereastra principala are patru taburi:

1. **Generare harta** - alegere seed, dimensiuni, densitate obstacole, preview
2. **Algoritmi** - rulare A* / Dijkstra / BFS / RRT pe harta curenta, cu plot traseu
3. **Reinforcement Learning** - antrenare Q-learning / SARSA / GA, comparatie politici
4. **Live monitor** - executie in CoppeliaSim cu pozitia robotului in timp real

Sub taburi exista un panou de log persistent.

## Utilizare CLI

### Generare harta aleatoare

```powershell
python -m nav_robot.cli generate --seed 42 --width 20 --height 20 --obstacles 0.25 --plot
```

Genereaza o harta 20x20 cu 25% obstacole, o salveaza in `data/maps/m42.json`
si produce `outputs/map_seed42.png`. Aceeasi valoare a `--seed` produce mereu aceeasi harta.

### Planificare offline

```powershell
python -m nav_robot.cli plan --map data/maps/m42.json --algo astar --plot
python -m nav_robot.cli compare --map data/maps/m42.json --plot
```

`compare` ruleaza A*, Dijkstra, BFS si RRT pe aceeasi harta si tipareste o tabela
cu lungimea drumului, costul, nodurile expandate si timpul, plus un plot suprapus.

### Trimite harta in CoppeliaSim

Necesita CoppeliaSim deschis cu scena `scenes/pioneer_nav.ttt` (Pioneer P3-DX)
si serverul ZMQ activ pe portul 23000.

```powershell
python -m nav_robot.cli build-scene --map data/maps/m42.json --place-robot
```

Creeaza in scena cate un cuboid (0.5 x 0.5 x 0.5 m) pentru fiecare celula de
obstacol, grupat sub dummy-ul `MapObstacles`. La urmatoarea rulare obstacolele
anterioare sunt sterse automat. Pentru a goli scena fara a regenera:

```powershell
python -m nav_robot.cli build-scene --clear-only
```

## Structura proiect

```
soft_roboti/
|-- README.md
|-- requirements.txt
|-- scenes/pioneer_nav.ttt
|-- src/nav_robot/
|   |-- cli.py            config.py
|   |-- map/              grid_map.py  generator.py  visualization.py
|   |-- planners/         base.py  astar.py  dijkstra.py  bfs.py  rrt.py
|   |-- reactive/         bug2.py  wall_following.py
|   |-- rl/               env.py  qlearning.py  sarsa.py  genetic.py
|   |                     policy.py  trainer.py  deploy.py  visualization.py
|   |-- coppelia/         client.py  robot.py  sensors.py  scene_builder.py
|   |-- controller/       waypoint_follower.py  differential_drive.py  runner.py
|   |-- gui/              app.py  main_window.py  log_widget.py  worker.py
|       |-- tabs/         map_tab.py  algorithm_tab.py  rl_tab.py  live_tab.py
|       |   |-- rl_subtabs/   qlearning_subtab.py  ga_subtab.py  compare_subtab.py
|-- data/maps/
|-- outputs/
|-- tests/
```

## Testare

```powershell
pip install pytest
pytest tests/
```

Acopera generatorul de harta, planificatorii (A*, Dijkstra, BFS, RRT), comportamentele
reactive, waypoint follower-ul si modulul de RL (Q-learning, SARSA, GA).
