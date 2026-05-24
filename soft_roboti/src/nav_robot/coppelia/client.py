"""Conexiune ZMQ Remote API catre CoppeliaSim (faza 3 - stub)."""

from __future__ import annotations

from nav_robot.config import COPPELIA_HOST, COPPELIA_PORT


def connect(host: str = COPPELIA_HOST, port: int = COPPELIA_PORT):
    """Stabileste conexiunea cu serverul CoppeliaSim.

    Returns:
        Tuplu (client, sim) - obiectele expuse de coppeliasim_zmqremoteapi_client.
    """
    raise NotImplementedError(
        "connect - TODO faza 3: from coppeliasim_zmqremoteapi_client import RemoteAPIClient; "
        "client = RemoteAPIClient(host, port); return client, client.require('sim'). "
        "(Vezi lab 06 cerinta 3.1.)"
    )
