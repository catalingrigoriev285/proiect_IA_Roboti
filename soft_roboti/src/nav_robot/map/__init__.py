"""Modulul map - reprezentarea si generarea hartilor 2D."""

from nav_robot.map.grid_map import GridMap
from nav_robot.map.generator import generate_random_map

__all__ = ["GridMap", "generate_random_map"]
