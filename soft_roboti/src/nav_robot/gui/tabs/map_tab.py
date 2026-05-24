"""Tab 1: generarea hartii cu configurari + trimitere in CoppeliaSim."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from nav_robot.config import (
    DEFAULT_CELL_SIZE, DEFAULT_GRID_H, DEFAULT_GRID_W,
    DEFAULT_OBSTACLE_RATIO, DEFAULT_SEED, MAPS_DIR, OUTPUTS_DIR,
)
from nav_robot.gui.worker import run_async
from nav_robot.map import GridMap, generate_random_map
from nav_robot.map.visualization import plot_map

log = logging.getLogger("gui.map")


class MapTab(QWidget):
    """Configurare + generare + preview + trimitere in CoppeliaSim."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_grid: GridMap | None = None
        self._thread = None
        self._worker = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Stanga: formular configurare (wrap in scroll pentru ferestre mici)
        form_box = self._wrap_scroll(self._build_form())
        # Dreapta: preview matplotlib
        preview_box = self._build_preview()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(form_box)
        splitter.addWidget(preview_box)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([380, 700])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(splitter)

    def _build_form(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap)
        v.setContentsMargins(4, 4, 4, 4)
        v.setSpacing(8)

        # --- Parametri harta ---
        gb_map = QGroupBox("Parametri harta")
        f = QFormLayout(gb_map)

        self.sp_seed = QSpinBox(); self.sp_seed.setRange(0, 1_000_000); self.sp_seed.setValue(DEFAULT_SEED)
        self.sp_width = QSpinBox(); self.sp_width.setRange(4, 200); self.sp_width.setValue(DEFAULT_GRID_W)
        self.sp_height = QSpinBox(); self.sp_height.setRange(4, 200); self.sp_height.setValue(DEFAULT_GRID_H)
        self.sp_obstacles = QDoubleSpinBox()
        self.sp_obstacles.setRange(0.0, 0.89); self.sp_obstacles.setSingleStep(0.05); self.sp_obstacles.setValue(DEFAULT_OBSTACLE_RATIO)
        self.sp_cell = QDoubleSpinBox()
        self.sp_cell.setRange(0.05, 5.0); self.sp_cell.setSingleStep(0.05); self.sp_cell.setValue(DEFAULT_CELL_SIZE); self.sp_cell.setSuffix(" m")

        f.addRow("Seed:", self.sp_seed)
        f.addRow("Latime (celule):", self.sp_width)
        f.addRow("Inaltime (celule):", self.sp_height)
        f.addRow("Fractie obstacole:", self.sp_obstacles)
        f.addRow("Dim celula:", self.sp_cell)

        # --- Parametri scena CoppeliaSim ---
        gb_scene = QGroupBox("Scena CoppeliaSim")
        f2 = QFormLayout(gb_scene)
        self.sp_obs_h = QDoubleSpinBox()
        self.sp_obs_h.setRange(0.05, 5.0); self.sp_obs_h.setSingleStep(0.1); self.sp_obs_h.setValue(0.5); self.sp_obs_h.setSuffix(" m")
        self.cb_floor = QCheckBox("Adauga floor (recomandat)"); self.cb_floor.setChecked(True)
        self.cb_place_robot = QCheckBox("Muta robotul in celula start"); self.cb_place_robot.setChecked(True)
        self.cb_realistic = QCheckBox("Obstacole realiste (modele 3D din ModelBrowser)")
        self.cb_realistic.setChecked(False)
        self.cb_theme = QComboBox(); self.cb_theme.addItems(["mobilier", "depozit", "strada", "mixt"])
        self.sp_realistic_seed = QSpinBox(); self.sp_realistic_seed.setRange(0, 1_000_000); self.sp_realistic_seed.setValue(7)
        f2.addRow("Inaltime obstacole:", self.sp_obs_h)
        f2.addRow("", self.cb_floor)
        f2.addRow("", self.cb_place_robot)
        f2.addRow("", self.cb_realistic)
        f2.addRow("Tema obiecte:", self.cb_theme)
        f2.addRow("Seed plasare:", self.sp_realistic_seed)

        # --- Butoane ---
        gb_actions = QGroupBox("Actiuni")
        v_a = QVBoxLayout(gb_actions)
        self.btn_generate = QPushButton("1. Genereaza harta")
        self.btn_save = QPushButton("2. Salveaza JSON")
        self.btn_load = QPushButton("Incarca JSON existent...")
        self.btn_build_scene = QPushButton("3. Trimite in CoppeliaSim")
        self.btn_clear_scene = QPushButton("Curata scena (sterge MapObstacles)")
        self.btn_reset_robot = QPushButton("Reseteaza robot la start")
        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)
        self.btn_build_scene.clicked.connect(self._on_build_scene)
        self.btn_clear_scene.clicked.connect(self._on_clear_scene)
        self.btn_reset_robot.clicked.connect(self._on_reset_robot)
        for b in (self.btn_generate, self.btn_save, self.btn_load,
                  self.btn_build_scene, self.btn_clear_scene, self.btn_reset_robot):
            v_a.addWidget(b)

        self.lbl_status = QLabel("Niciuna generata.")
        self.lbl_status.setStyleSheet("color:#888;")

        v.addWidget(gb_map)
        v.addWidget(gb_scene)
        v.addWidget(gb_actions)
        v.addWidget(self.lbl_status)
        v.addStretch(1)
        return wrap

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        """Pune `widget` intr-un QScrollArea cu scroll vertical, ca sa nu
        blocheze resize-ul ferestrei principale."""
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def _build_preview(self) -> QWidget:
        wrap = QFrame()
        wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap)
        v.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Preview harta")
        title.setStyleSheet("font-weight:bold;")
        v.addWidget(title)

        self.figure = Figure(figsize=(6, 6), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        v.addWidget(self.canvas, stretch=1)
        return wrap

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_generate(self) -> None:
        try:
            grid = generate_random_map(
                width=self.sp_width.value(),
                height=self.sp_height.value(),
                obstacle_ratio=self.sp_obstacles.value(),
                seed=self.sp_seed.value(),
                cell_size=self.sp_cell.value(),
            )
        except Exception as e:
            log.error("Generare esuata: %s", e)
            QMessageBox.critical(self, "Eroare generare", str(e))
            return

        self.current_grid = grid
        n_obs = int(grid.cells.sum())
        log.info("Harta generata: %dx%d, %d obstacole, seed=%d",
                 grid.width, grid.height, n_obs, grid.seed or -1)
        self.lbl_status.setText(
            f"Generata: {grid.width}x{grid.height}, {n_obs} obstacole, "
            f"start={grid.start}, goal={grid.goal}"
        )
        self._refresh_preview()

    def _on_save(self) -> None:
        if self.current_grid is None:
            QMessageBox.warning(self, "Nimic de salvat", "Genereaza intai o harta.")
            return
        default = MAPS_DIR / f"m{self.current_grid.seed}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Salveaza harta", str(default), "JSON (*.json)"
        )
        if not path:
            return
        saved = self.current_grid.save(path)
        log.info("Harta salvata in %s", saved)
        QMessageBox.information(self, "Salvat", f"Harta salvata in:\n{saved}")

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Incarca harta", str(MAPS_DIR), "JSON (*.json)"
        )
        if not path:
            return
        try:
            grid = GridMap.load(path)
        except Exception as e:
            log.error("Incarcare esuata: %s", e)
            QMessageBox.critical(self, "Eroare incarcare", str(e))
            return
        self.current_grid = grid
        log.info("Harta incarcata din %s (seed=%s)", path, grid.seed)
        # Sincronizeaza UI cu valorile din JSON
        if grid.seed is not None:
            self.sp_seed.setValue(int(grid.seed))
        self.sp_width.setValue(grid.width)
        self.sp_height.setValue(grid.height)
        self.sp_cell.setValue(grid.cell_size)
        self.lbl_status.setText(
            f"Incarcata din disc: {grid.width}x{grid.height}, "
            f"{int(grid.cells.sum())} obstacole."
        )
        self._refresh_preview()

    def _on_build_scene(self) -> None:
        if self.current_grid is None:
            QMessageBox.warning(self, "Nimic de trimis",
                                "Genereaza sau incarca intai o harta.")
            return
        grid = self.current_grid
        place_robot = self.cb_place_robot.isChecked()
        with_floor = self.cb_floor.isChecked()
        obs_h = self.sp_obs_h.value()
        realistic = self.cb_realistic.isChecked()
        theme = self.cb_theme.currentText()
        rseed = self.sp_realistic_seed.value()
        log.info("Conectare la CoppeliaSim si construire scena %s ...",
                 f"REALISTA (tema={theme})" if realistic else "(cuboizi)")
        self.btn_build_scene.setEnabled(False)

        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.scene_builder import (
                build_obstacles_from_map, build_realistic_obstacles_from_map,
                place_robot_at_start,
            )
            _, sim = connect()
            if realistic:
                parent, handles = build_realistic_obstacles_from_map(
                    sim, grid, theme=theme, with_floor=with_floor,
                    height_m=obs_h, seed=rseed,
                )
            else:
                parent, handles = build_obstacles_from_map(
                    sim, grid, height_m=obs_h, with_floor=with_floor,
                )
            if place_robot:
                place_robot_at_start(sim, grid)
            return (parent, len(handles), place_robot, with_floor, realistic)

        def done(result):
            self.btn_build_scene.setEnabled(True)
            parent, n, placed, floor, realistic_flag = result
            extra = " + floor" if floor else ""
            kind = " realiste" if realistic_flag else ""
            msg = f"Plasate {n} obiecte{kind}{extra} (parent handle={parent})."
            if placed:
                msg += f" Robot mutat la {grid.start}."
            log.info(msg)

        def fail(err):
            self.btn_build_scene.setEnabled(True)
            log.error("Build scena esuat: %s", err)
            QMessageBox.critical(self, "Eroare CoppeliaSim", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_reset_robot(self) -> None:
        if self.current_grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza intai o harta cu un start definit.")
            return
        grid = self.current_grid
        log.info("Reset robot la start=%s ...", grid.start)
        self.btn_reset_robot.setEnabled(False)

        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.scene_builder import reset_robot_to_start
            _, sim = connect()
            return reset_robot_to_start(sim, grid)

        def done(info):
            self.btn_reset_robot.setEnabled(True)
            sx, sy, _ = info["position"]
            msg = f"Robot resetat la ({sx:.2f}, {sy:.2f})."
            if info["was_running"]:
                msg += " Sim oprita, repozitionata"
                if info["restarted"]:
                    msg += " si repornita."
                else:
                    msg += "; reporneste manual cu Play."
            else:
                msg += " (Sim era oprita - apasa Play in CoppeliaSim.)"
            log.info(msg)

        def fail(err):
            self.btn_reset_robot.setEnabled(True)
            log.error("Reset robot esuat: %s", err)
            QMessageBox.critical(self, "Eroare CoppeliaSim", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_clear_scene(self) -> None:
        log.info("Curatare scena CoppeliaSim ...")

        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.scene_builder import clear_obstacles_by_alias
            _, sim = connect()
            return clear_obstacles_by_alias(sim)

        def done(n):
            log.info("Sterse %d obiecte din MapObstacles.", n)

        def fail(err):
            log.error("Curatare esuata: %s", err)
            QMessageBox.critical(self, "Eroare CoppeliaSim", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    # ------------------------------------------------------------------
    def _refresh_preview(self) -> None:
        self.figure.clear()
        if self.current_grid is None:
            self.canvas.draw_idle()
            return
        ax = self.figure.add_subplot(111)
        plot_map(self.current_grid, ax=ax)
        self.canvas.draw_idle()
