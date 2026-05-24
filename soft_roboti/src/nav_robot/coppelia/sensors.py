"""Citirea senzorilor ultrasonici (faza 3 - stub, portare lab 06 cerinta 3.3)."""

from __future__ import annotations

from nav_robot.config import SENSOR_MAX_RANGE


def read_all_sensors(sim, sensors: list[int]) -> list[tuple[bool, float]]:
    """Citeste toti senzorii si returneaza (detectat, distanta_m) per senzor.

    Cand nu se detecteaza nimic se returneaza (False, SENSOR_MAX_RANGE).
    """
    raise NotImplementedError(
        "read_all_sensors - TODO faza 3: for s in sensors: sim.readProximitySensor(s). "
        "(Vezi lab 06 cerinta 3.3.)"
    )


def min_distance(readings: list[tuple[bool, float]], indices: list[int]) -> float:
    """Distanta minima detectata in subset-ul de senzori."""
    raise NotImplementedError(
        "min_distance - TODO faza 3: filtreaza dupa indices, returneaza min sau SENSOR_MAX_RANGE."
    )
