"""Teste pentru generator-ul de harti aleatoare."""

import json
import numpy as np
import pytest

from nav_robot.map import GridMap, generate_random_map
from nav_robot.map.generator import _connected


def test_seed_reproducible():
    a = generate_random_map(width=15, height=15, obstacle_ratio=0.2, seed=42)
    b = generate_random_map(width=15, height=15, obstacle_ratio=0.2, seed=42)
    assert np.array_equal(a.cells, b.cells)
    assert a.start == b.start and a.goal == b.goal


def test_different_seeds_differ():
    a = generate_random_map(width=15, height=15, obstacle_ratio=0.25, seed=1)
    b = generate_random_map(width=15, height=15, obstacle_ratio=0.25, seed=2)
    assert not np.array_equal(a.cells, b.cells)


def test_start_and_goal_free():
    g = generate_random_map(width=20, height=20, obstacle_ratio=0.3, seed=7)
    assert g.is_free(g.start)
    assert g.is_free(g.goal)


def test_start_and_goal_connected():
    for seed in (1, 7, 42, 100, 999):
        g = generate_random_map(width=20, height=20, obstacle_ratio=0.3, seed=seed)
        assert _connected(g.cells, g.start, g.goal), f"seed={seed} are start/goal deconectate"


def test_dimensions_match():
    g = generate_random_map(width=12, height=18, obstacle_ratio=0.1, seed=0)
    assert g.cells.shape == (18, 12)
    assert g.width == 12 and g.height == 18


def test_border_is_free():
    g = generate_random_map(width=20, height=20, obstacle_ratio=0.4, seed=3)
    assert (g.cells[0, :] == 0).all()
    assert (g.cells[-1, :] == 0).all()
    assert (g.cells[:, 0] == 0).all()
    assert (g.cells[:, -1] == 0).all()


def test_save_load_roundtrip(tmp_path):
    g = generate_random_map(width=10, height=10, obstacle_ratio=0.2, seed=5)
    out = g.save(tmp_path / "m.json")
    loaded = GridMap.load(out)
    assert np.array_equal(g.cells, loaded.cells)
    assert g.start == loaded.start
    assert g.goal == loaded.goal
    assert g.seed == loaded.seed


def test_invalid_params():
    with pytest.raises(ValueError):
        generate_random_map(width=2, height=2)
    with pytest.raises(ValueError):
        generate_random_map(obstacle_ratio=0.95)


def test_to_world_round_trip():
    g = generate_random_map(width=10, height=10, obstacle_ratio=0.0, seed=0,
                            start=(1, 1), goal=(8, 8))
    cell = (3, 4)
    wx, wy = g.to_world(cell)
    assert g.from_world(wx, wy) == cell


def test_neighbors_4_and_8():
    g = generate_random_map(width=10, height=10, obstacle_ratio=0.0, seed=0)
    n4 = g.neighbors((5, 5), diagonal=False)
    n8 = g.neighbors((5, 5), diagonal=True)
    assert len(n4) == 4
    assert len(n8) == 8
