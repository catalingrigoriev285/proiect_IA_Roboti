"""Wall-following: urmarirea unui perete (faza 4 - stub).

Refactorizat din lab 06 cerinta 3.6 - controller proportional pe distanta
fata de peretele drept, plus reactie la obstacole frontale.
"""

from __future__ import annotations


def wall_follow_step(distances_right: list[float], distance_front: float,
                     v_base: float = 2.0, target_dist: float = 0.4,
                     k_p: float = 3.0, front_stop: float = 0.4) -> tuple[float, float]:
    """Calculeaza vitezele (v_left, v_right) pentru o iteratie de wall-following.

    Args:
        distances_right: lecturi de la senzorii laterali drepti (m).
        distance_front: distanta minima detectata frontal (m).
        v_base: viteza nominala (rad/s).
        target_dist: distanta dorita fata de perete (m).
        k_p: castigul controller-ului proportional.
        front_stop: distanta de declansare a virajului la stanga (m).
    """
    raise NotImplementedError(
        "wall_follow_step - TODO faza 4: portare lab 06 cerinta 3.6 cu refactor in functie pura."
    )
