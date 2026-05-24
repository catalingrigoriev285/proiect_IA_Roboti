"""Cinematica diferentiala Pioneer P3-DX (faza 3 - stub).

Conversii intre (v_lin, omega) si (v_left, v_right) in rad/s, conform
formulei din lab 06 sectiunea 2.2:

    v_lin   = R * (v_left + v_right) / 2
    omega   = R * (v_right - v_left) / L

unde R = raza rotii, L = distanta intre roti.
"""

from __future__ import annotations

from nav_robot.config import ROBOT_WHEEL_BASE, ROBOT_WHEEL_RADIUS


def cmd_to_wheels(v_lin: float, omega: float,
                  wheel_radius: float = ROBOT_WHEEL_RADIUS,
                  wheel_base: float = ROBOT_WHEEL_BASE) -> tuple[float, float]:
    """Converteste (viteza liniara m/s, viteza unghiulara rad/s) in (v_left, v_right) rad/s."""
    raise NotImplementedError(
        "cmd_to_wheels - TODO faza 3: aplica formulele inverse din lab 06 §2.2."
    )


def wheels_to_cmd(v_left: float, v_right: float,
                  wheel_radius: float = ROBOT_WHEEL_RADIUS,
                  wheel_base: float = ROBOT_WHEEL_BASE) -> tuple[float, float]:
    """Inversul lui cmd_to_wheels: din vitezele rotilor -> (v_lin, omega)."""
    raise NotImplementedError("wheels_to_cmd - TODO faza 3.")
