"""Cinematica diferentiala Pioneer P3-DX (lab 06 §2.2).

Conversii intre (v_lin, omega) si (v_left, v_right) in rad/s:

    v_lin   = R * (v_left + v_right) / 2          [m/s]
    omega   = R * (v_right - v_left) / L          [rad/s]

Inversele (folosite pentru controlere):

    v_left  = (2 * v_lin - omega * L) / (2 * R)
    v_right = (2 * v_lin + omega * L) / (2 * R)

unde R = raza rotii, L = distanta intre roti (wheel base).
"""

from __future__ import annotations

from nav_robot.config import ROBOT_WHEEL_BASE, ROBOT_WHEEL_RADIUS


def cmd_to_wheels(v_lin: float, omega: float,
                  wheel_radius: float = ROBOT_WHEEL_RADIUS,
                  wheel_base: float = ROBOT_WHEEL_BASE) -> tuple[float, float]:
    """Converteste (viteza liniara m/s, viteza unghiulara rad/s) in (v_left, v_right) rad/s."""
    v_left = (2.0 * v_lin - omega * wheel_base) / (2.0 * wheel_radius)
    v_right = (2.0 * v_lin + omega * wheel_base) / (2.0 * wheel_radius)
    return v_left, v_right


def wheels_to_cmd(v_left: float, v_right: float,
                  wheel_radius: float = ROBOT_WHEEL_RADIUS,
                  wheel_base: float = ROBOT_WHEEL_BASE) -> tuple[float, float]:
    """Inversul lui cmd_to_wheels: din vitezele rotilor -> (v_lin, omega)."""
    v_lin = wheel_radius * (v_left + v_right) / 2.0
    omega = wheel_radius * (v_right - v_left) / wheel_base
    return v_lin, omega


def clamp_wheels(v_left: float, v_right: float,
                 v_max: float) -> tuple[float, float]:
    """Limiteaza vitezele rotilor in [-v_max, v_max] pastrand raportul (daca posibil)."""
    peak = max(abs(v_left), abs(v_right))
    if peak <= v_max:
        return v_left, v_right
    scale = v_max / peak
    return v_left * scale, v_right * scale
