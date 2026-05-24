"""Wall-following: pas pur Python pentru un controller P pe perete (lab 06 §3.6)."""

from __future__ import annotations

from nav_robot.config import ROBOT_BASE_VELOCITY, SENSOR_MAX_RANGE


# Indecsi senzori frontali si laterali pentru robotul Pioneer P3-DX (din lab 06)
FRONT_SENSORS = [3, 4]
RIGHT_SENSORS = [8, 9]
LEFT_SENSORS = [14, 15]


def wall_follow_step(
    distance_right: float,
    distance_front: float,
    v_base: float = ROBOT_BASE_VELOCITY,
    target_dist: float = 0.4,
    k_p: float = 3.0,
    front_stop: float = 0.4,
    sensor_max: float = SENSOR_MAX_RANGE,
) -> tuple[float, float, str]:
    """Returneaza (v_left, v_right, state_label) pentru o iteratie de wall-following dreapta.

    Args:
        distance_right: distanta minima la senzorii laterali drepti (m).
        distance_front: distanta minima frontala (m).
        v_base: viteza nominala (rad/s).
        target_dist: distanta dorita fata de peretele drept (m).
        k_p: castigul P-controller-ului.
        front_stop: distanta de declansare a virajului la stanga cand obstacol frontal.
        sensor_max: valoarea returnata cand nu se detecteaza nimic.
    """
    # Obstacol frontal: viraj brusc la stanga
    if distance_front < front_stop:
        return -v_base, +v_base, "VIREAZA-STANGA"

    # Nu vedem peretele: cauta-l (viraj usor dreapta)
    if distance_right >= sensor_max * 0.95:
        return v_base, v_base * 0.5, "CAUTA-PERETE"

    # Controller proportional pe distanta fata de perete
    error = distance_right - target_dist
    v_left = v_base + k_p * error
    v_right = v_base - k_p * error
    cap = v_base * 1.5
    v_left = max(-cap, min(cap, v_left))
    v_right = max(-cap, min(cap, v_right))
    return v_left, v_right, "URMARIRE"
