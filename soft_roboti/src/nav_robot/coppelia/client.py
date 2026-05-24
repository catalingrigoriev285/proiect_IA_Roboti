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


def ensure_simulation_running(sim, timeout_s: float = 3.0,
                              poll_dt: float = 0.05) -> bool:
    """Asigura ca simularea CoppeliaSim este in stare `advancing_running`.

    Daca sim este oprita, o porneste; daca este in paused/first-after-stop,
    asteapta sa devina running pana la `timeout_s`. Necesar inainte de a trimite
    comenzi `setJointTargetVelocity`, altfel comenzile sunt ignorate / robotul
    nu se misca pana la primul tick efectiv.

    Returns:
        True daca am ajuns la `advancing_running`, False la timeout.
    """
    import time

    try:
        state = sim.getSimulationState()
    except Exception:
        return False

    if state == sim.simulation_stopped:
        try:
            sim.startSimulation()
        except Exception:
            return False

    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            state = sim.getSimulationState()
        except Exception:
            return False
        if state == sim.simulation_advancing_running:
            return True
        time.sleep(poll_dt)
    return False
