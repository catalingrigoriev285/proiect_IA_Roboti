"""Conexiune ZMQ Remote API catre CoppeliaSim."""

from __future__ import annotations

from nav_robot.config import COPPELIA_HOST, COPPELIA_PORT


def connect(host: str = COPPELIA_HOST, port: int = COPPELIA_PORT):
    """Stabileste conexiunea cu serverul CoppeliaSim.

    Returns:
        Tuplu (client, sim) - obiectele expuse de coppeliasim_zmqremoteapi_client.

    Raises:
        ConnectionError: daca CoppeliaSim nu este deschis sau portul nu raspunde.
    """
    try:
        from coppeliasim_zmqremoteapi_client import RemoteAPIClient
    except ImportError as e:
        raise ImportError(
            "Pachetul 'coppeliasim-zmqremoteapi-client' nu este instalat. "
            "Ruleaza: pip install coppeliasim-zmqremoteapi-client"
        ) from e

    try:
        client = RemoteAPIClient(host, port)
        sim = client.require("sim")
    except Exception as e:
        raise ConnectionError(
            f"Nu pot conecta la CoppeliaSim ({host}:{port}). "
            "Verifica ca aplicatia este deschisa si scena este incarcata."
        ) from e

    return client, sim
