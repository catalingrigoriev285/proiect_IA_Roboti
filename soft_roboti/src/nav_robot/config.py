"""Constante centralizate pentru proiectul nav_robot."""

from pathlib import Path

# --- Harta ---
DEFAULT_GRID_W: int = 20
DEFAULT_GRID_H: int = 20
DEFAULT_OBSTACLE_RATIO: float = 0.25
DEFAULT_CELL_SIZE: float = 0.5  # metri per celula in scena CoppeliaSim

# --- Generator ---
DEFAULT_SEED: int = 42
MAX_GENERATION_RETRIES: int = 20  # incercari pentru a obtine harta cu start-goal conectate

# --- Robot Pioneer P3-DX (din lab 06) ---
ROBOT_BASE_VELOCITY: float = 2.0   # rad/s
ROBOT_MAX_VELOCITY: float = 6.0    # rad/s
ROBOT_WHEEL_RADIUS: float = 0.0975  # m
ROBOT_WHEEL_BASE: float = 0.331    # m (distanta intre roti)

# --- Senzori ---
SENSOR_MAX_RANGE: float = 1.0      # metri
SENSOR_COUNT: int = 16

# --- CoppeliaSim ---
COPPELIA_HOST: str = "localhost"
COPPELIA_PORT: int = 23000
COPPELIA_SCENE_PATH: str = "scenes/pioneer_nav.ttt"

# --- Caile proiectului ---
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = PROJECT_ROOT / "data"
MAPS_DIR: Path = DATA_DIR / "maps"
OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"
