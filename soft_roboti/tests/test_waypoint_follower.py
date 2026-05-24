"""Teste pure Python pentru WaypointFollower si differential_drive."""

import math

import pytest

from nav_robot.controller.differential_drive import (
    cmd_to_wheels, wheels_to_cmd, clamp_wheels,
)
from nav_robot.controller.waypoint_follower import WaypointFollower, wrap_to_pi


# ----------------------------------------------------------------------
# Cinematica diferentiala
# ----------------------------------------------------------------------
class TestDifferentialDrive:
    def test_straight_forward_equal_wheels(self):
        v_l, v_r = cmd_to_wheels(v_lin=0.5, omega=0.0)
        assert v_l == pytest.approx(v_r)
        assert v_l > 0

    def test_pure_rotation_opposite_wheels(self):
        v_l, v_r = cmd_to_wheels(v_lin=0.0, omega=1.0)
        assert v_l == pytest.approx(-v_r)
        assert v_r > 0   # omega pozitiv -> roata dreapta inainte

    def test_roundtrip(self):
        for v_lin, omega in [(0.3, 0.0), (0.0, 1.5), (0.4, -0.7), (-0.2, 0.2)]:
            v_l, v_r = cmd_to_wheels(v_lin, omega)
            v_lin_back, omega_back = wheels_to_cmd(v_l, v_r)
            assert v_lin_back == pytest.approx(v_lin, abs=1e-9)
            assert omega_back == pytest.approx(omega, abs=1e-9)

    def test_clamp_preserves_ratio(self):
        v_l, v_r = clamp_wheels(10.0, 4.0, v_max=5.0)
        assert v_l == pytest.approx(5.0)
        assert v_r == pytest.approx(2.0)

    def test_clamp_negatives(self):
        v_l, v_r = clamp_wheels(-8.0, 2.0, v_max=4.0)
        assert v_l == pytest.approx(-4.0)
        assert v_r == pytest.approx(1.0)

    def test_clamp_noop(self):
        v_l, v_r = clamp_wheels(2.0, 3.0, v_max=5.0)
        assert v_l == 2.0 and v_r == 3.0


# ----------------------------------------------------------------------
# wrap_to_pi
# ----------------------------------------------------------------------
class TestWrapToPi:
    def test_inside_range(self):
        assert wrap_to_pi(0.5) == pytest.approx(0.5)

    def test_wrap_positive(self):
        # 3*pi/2 -> -pi/2
        assert wrap_to_pi(3 * math.pi / 2) == pytest.approx(-math.pi / 2, abs=1e-9)

    def test_wrap_negative(self):
        assert wrap_to_pi(-3 * math.pi / 2) == pytest.approx(math.pi / 2, abs=1e-9)


# ----------------------------------------------------------------------
# WaypointFollower
# ----------------------------------------------------------------------
class TestWaypointFollower:
    def test_done_when_empty(self):
        wf = WaypointFollower([])
        assert wf.is_done()
        v_l, v_r = wf.step(0.0, 0.0, 0.0)
        assert v_l == 0.0 and v_r == 0.0

    def test_advances_when_in_tolerance(self):
        wf = WaypointFollower([(1.0, 0.0), (2.0, 0.0)], tolerance_m=0.2)
        # La pozitia (0.95, 0.0) suntem in tolerance fata de (1.0, 0.0)
        wf.step(0.95, 0.0, 0.0)
        assert wf.index >= 1

    def test_straight_ahead_yields_symmetric_velocities(self):
        wf = WaypointFollower([(2.0, 0.0)], tolerance_m=0.1)
        # Robot la origine, orientat catre +X (yaw=0), tinta drept inainte
        v_l, v_r = wf.step(0.0, 0.0, 0.0)
        assert v_l == pytest.approx(v_r, abs=1e-9)
        assert v_l > 0

    def test_left_turn_when_target_on_left(self):
        wf = WaypointFollower([(0.0, 2.0)])
        # Tinta este la stanga (y+); robot orientat catre +X
        v_l, v_r = wf.step(0.0, 0.0, 0.0)
        # Pentru viraj la stanga: roata dreapta mai rapida
        assert v_r > v_l

    def test_right_turn_when_target_on_right(self):
        wf = WaypointFollower([(0.0, -2.0)])
        v_l, v_r = wf.step(0.0, 0.0, 0.0)
        assert v_l > v_r

    def test_simulated_path_converges(self):
        """Simulator simplu de tip integrare Euler care verifica convergenta la goal."""
        wf = WaypointFollower([(2.0, 2.0)], v_lin=0.3, tolerance_m=0.1)
        x, y, yaw = 0.0, 0.0, 0.0
        dt = 0.05
        for _ in range(2000):
            if wf.is_done():
                break
            v_l, v_r = wf.step(x, y, yaw)
            # Cinematica diferentiala inversa pentru a obtine v_lin, omega
            v_lin, omega = wheels_to_cmd(v_l, v_r)
            x += v_lin * math.cos(yaw) * dt
            y += v_lin * math.sin(yaw) * dt
            yaw = wrap_to_pi(yaw + omega * dt)
        assert wf.is_done()
        assert math.hypot(x - 2.0, y - 2.0) < 0.2
