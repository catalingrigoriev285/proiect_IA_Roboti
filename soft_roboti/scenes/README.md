# Scene CoppeliaSim

Acest director contine scena `.ttt` folosita de proiect.

## Cerinte

Scena trebuie sa contina:

- Un **Pioneer P3-DX** la origine `(0, 0, 0.139)` orientat catre `+X`.
- Cei 16 senzori ultrasonici activi (ierarhie standard `/PioneerP3DX/ultrasonicSensor[0..15]`).
- Nicio cutie / obstacol fix in scena - obstacolele sunt adaugate dinamic
  de modulul `nav_robot.coppelia.scene_builder` pe baza hartii generate.

## Pornire rapida

1. Deschideti CoppeliaSim si scena `pioneer_lab06.ttt` din laboratorul 06.
2. Stergeti orice obstacole existente (lasati doar robotul si podeaua).
3. Salvati ca `pioneer_nav.ttt` in acest director.
4. In CoppeliaSim apasati Play (>) inainte sa rulati scripturile Python.

Calea implicita asteptata de cod este `scenes/pioneer_nav.ttt`
(configurabila in `src/nav_robot/config.py`).
