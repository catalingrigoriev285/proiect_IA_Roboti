"""Citirea senzorilor ultrasonici (portare lab 06 cerinta 3.3)."""

from __future__ import annotations

from nav_robot.config import SENSOR_MAX_RANGE


SensorReading = tuple[bool, float]   # (detectat, distanta_m)


def read_all_sensors(sim, sensors: list[int]) -> list[SensorReading]:
    """Citeste toti senzorii si returneaza lista (detectat, distanta_m) per senzor.

    Cand nu se detecteaza nimic, distanta returnata este `SENSOR_MAX_RANGE`.
    """
    out: list[SensorReading] = []
    for s in sensors:
        result, distance, *_ = sim.readProximitySensor(s)
        detected = bool(result)
        dist = float(distance) if detected else SENSOR_MAX_RANGE
        out.append((detected, dist))
    return out


def min_distance(readings: list[SensorReading], indices: list[int]) -> float:
    """Distanta minima detectata in subsetul de senzori dat de `indices`.

    Returneaza `SENSOR_MAX_RANGE` daca niciun senzor din subset nu detecteaza.
    """
    md = SENSOR_MAX_RANGE
    for i in indices:
        det, dist = readings[i]
        if det and dist < md:
            md = dist
    return md
