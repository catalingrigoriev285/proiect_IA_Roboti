"""Teste pentru wall_following + Bug2 (parti pure, fara CoppeliaSim)."""

import math

import pytest

from nav_robot.reactive.bug2 import _distance_to_m_line
from nav_robot.reactive.wall_following import wall_follow_step


# ----------------------------------------------------------------------
# wall_follow_step
# ----------------------------------------------------------------------
class TestWallFollow:
    def test_front_obstacle_turns_left(self):
        v_l, v_r, state = wall_follow_step(distance_right=0.4, distance_front=0.2)
        assert v_l < 0 and v_r > 0
        assert state == "VIREAZA-STANGA"

    def test_no_wall_seeks_right(self):
        # Distanta dreapta = SENSOR_MAX -> nu detecteaza perete
        v_l, v_r, state = wall_follow_step(distance_right=1.0, distance_front=1.0)
        assert v_l > v_r
        assert state == "CAUTA-PERETE"

    def test_p_controller_too_far(self):
        # Prea departe de perete (eroare > 0) -> viraj catre perete (dreapta)
        v_l, v_r, state = wall_follow_step(distance_right=0.7, distance_front=1.0,
                                           target_dist=0.4)
        assert v_l > v_r
        assert state == "URMARIRE"

    def test_p_controller_too_close(self):
        # Prea aproape (eroare < 0) -> viraj catre stanga
        v_l, v_r, state = wall_follow_step(distance_right=0.2, distance_front=1.0,
                                           target_dist=0.4)
        assert v_r > v_l
        assert state == "URMARIRE"


# ----------------------------------------------------------------------
# _distance_to_m_line
# ----------------------------------------------------------------------
class TestDistanceToMLine:
    def test_zero_on_line(self):
        # m-line de la (0,0) la (10,0), punct (5, 0) este pe linie
        assert _distance_to_m_line(5.0, 0.0, 0.0, 0.0, 10.0, 0.0) == pytest.approx(0.0)

    def test_perpendicular_distance(self):
        # m-line orizontala; un punct la y=2 este la distanta 2
        d = _distance_to_m_line(5.0, 2.0, 0.0, 0.0, 10.0, 0.0)
        assert d == pytest.approx(2.0)

    def test_diagonal_line(self):
        # m-line de la (0,0) la (1,1); un punct la (1, 0) este la dist sqrt(2)/2
        d = _distance_to_m_line(1.0, 0.0, 0.0, 0.0, 1.0, 1.0)
        assert d == pytest.approx(math.sqrt(2) / 2, abs=1e-9)
