"""Sub-tab pentru Algoritm Genetic (PyGAD, cf. lab 09) pe politici per-celula."""

from __future__ import annotations

import logging

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QGroupBox, QLabel, QMessageBox, QPushButton, QSpinBox, QSplitter,
    QVBoxLayout, QWidget,
)

from nav_robot.gui.worker import run_async
from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.genetic import PolicyGA
from nav_robot.rl.trainer import evaluate_policy
from nav_robot.rl.visualization import plot_ga_convergence, plot_policy_arrows

log = logging.getLogger("gui.rl.ga")


class GASubTab(QWidget):
    """Configurare + antrenare cu PyGAD + vizualizare convergenta."""

    progress_signal = Signal(int, int, float, float)   # gen, total, best, mean

    def __init__(self, map_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab
        self.last_ga: PolicyGA | None = None
        self._stop_requested = False
        self._thread = None
        self._worker = None
        self._build_ui()
        self.progress_signal.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)

    def _build_ui(self) -> None:
        left = self._build_config()
        right = self._build_stats()
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0, 0); splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 700])
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(splitter)

    def _build_config(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap); v.setSpacing(8); v.setContentsMargins(4, 4, 4, 4)

        gb = QGroupBox("Parametri GA (PyGAD, cf. lab 09)")
        f = QFormLayout(gb)
        self.sp_pop = QSpinBox(); self.sp_pop.setRange(10, 1000); self.sp_pop.setValue(80)
        self.sp_gen = QSpinBox(); self.sp_gen.setRange(5, 5000); self.sp_gen.setValue(100)
        self.sp_mut = QDoubleSpinBox(); self.sp_mut.setRange(0.1, 50.0); self.sp_mut.setSingleStep(0.5); self.sp_mut.setValue(8.0); self.sp_mut.setSuffix(" %")
        self.sp_elite = QSpinBox(); self.sp_elite.setRange(0, 20); self.sp_elite.setValue(2)
        self.sp_kt = QSpinBox(); self.sp_kt.setRange(2, 20); self.sp_kt.setValue(3)
        self.cb_sel = QComboBox(); self.cb_sel.addItems(["tournament", "rws", "rank", "sus"])
        self.cb_diag = QComboBox(); self.cb_diag.addItems(["4 actiuni", "8 actiuni"])
        self.sp_rollouts = QSpinBox(); self.sp_rollouts.setRange(1, 10); self.sp_rollouts.setValue(1)
        self.sp_seed = QSpinBox(); self.sp_seed.setRange(0, 1_000_000); self.sp_seed.setValue(42)
        f.addRow("Pop size:", self.sp_pop)
        f.addRow("Generatii:", self.sp_gen)
        f.addRow("Mutatie:", self.sp_mut)
        f.addRow("Elitism:", self.sp_elite)
        f.addRow("K turneu:", self.sp_kt)
        f.addRow("Selectie:", self.cb_sel)
        f.addRow("Actiuni:", self.cb_diag)
        f.addRow("Rollouts/eval:", self.sp_rollouts)
        f.addRow("Seed:", self.sp_seed)

        gb_b = QGroupBox("Actiuni")
        v_b = QVBoxLayout(gb_b)
        self.btn_train = QPushButton("Antreneaza GA")
        self.btn_stop = QPushButton("Stop")
        self.btn_run = QPushButton("Ruleaza in CoppeliaSim")
        self.btn_save = QPushButton("Salveaza politica...")
        self.btn_train.clicked.connect(self._on_train)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_save.clicked.connect(self._on_save)
        for b in (self.btn_train, self.btn_stop, self.btn_run, self.btn_save):
            v_b.addWidget(b)

        self.lbl_status = QLabel("Astept...")
        self.lbl_status.setStyleSheet("color:#888;")
        self.lbl_status.setWordWrap(True)

        v.addWidget(gb); v.addWidget(gb_b); v.addWidget(self.lbl_status); v.addStretch(1)
        return wrap

    def _build_stats(self) -> QWidget:
        wrap = QFrame(); wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap); v.setContentsMargins(4, 4, 4, 4)
        title = QLabel("Convergenta GA + politica finala")
        title.setStyleSheet("font-weight:bold;")
        v.addWidget(title)
        self.figure = Figure(figsize=(8, 6), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        v.addWidget(self.canvas, stretch=1)
        return wrap

    # ------------------------------------------------------------------
    def _on_train(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta", "Genereaza intai o harta.")
            return
        diagonal = self.cb_diag.currentIndex() == 1
        env = GridWorldEnv(grid, diagonal=diagonal, seed=self.sp_seed.value())
        ga = PolicyGA(env,
                      pop_size=self.sp_pop.value(),
                      n_generations=self.sp_gen.value(),
                      mutation_percent_genes=self.sp_mut.value(),
                      keep_elitism=self.sp_elite.value(),
                      k_tournament=self.sp_kt.value(),
                      selection=self.cb_sel.currentText(),
                      n_rollouts_per_eval=self.sp_rollouts.value(),
                      seed=self.sp_seed.value())
        self._stop_requested = False
        self.btn_train.setEnabled(False)
        log.info("GA: pop=%d, gen=%d, mut=%.1f%%", self.sp_pop.value(),
                 self.sp_gen.value(), self.sp_mut.value())
        sig = self.progress_signal
        total = self.sp_gen.value()

        def task():
            def on_gen(g, stats):
                if g % 5 == 0 or g == total:
                    sig.emit(g, total, stats.best_fitness[-1], stats.mean_fitness[-1])
            stats = ga.run(on_generation=on_gen,
                           should_stop=lambda: self._stop_requested)
            return ga, stats

        def done(result):
            ga_obj, stats = result
            self.btn_train.setEnabled(True)
            self.last_ga = ga_obj
            metrics = evaluate_policy(env, ga_obj.policy(), n_episodes=20)
            self.lbl_status.setText(
                f"Gata. Best fitness={max(stats.best_fitness):.1f}, "
                f"eval success={metrics['success_rate']*100:.0f}%, "
                f"steps={metrics['mean_steps']:.1f}"
            )
            log.info("GA evaluare: success=%.0f%% reward=%.1f",
                     metrics['success_rate']*100, metrics['mean_reward'])
            self._refresh_plots(grid, ga_obj, stats)

        def fail(err):
            self.btn_train.setEnabled(True)
            log.error("GA esuat: %s", err)
            QMessageBox.critical(self, "Eroare GA", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_stop(self) -> None:
        self._stop_requested = True
        log.info("Stop GA solicitat.")

    def _on_run(self) -> None:
        if self.last_ga is None:
            QMessageBox.warning(self, "Nicio politica", "Antreneaza intai GA.")
            return
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta", "Trimite harta in CoppeliaSim.")
            return
        policy = self.last_ga.policy()
        log.info("Pornesc politica GA in CoppeliaSim.")
        self._stop_requested = False
        self.btn_run.setEnabled(False)
        diagonal = self.cb_diag.currentIndex() == 1

        def task():
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.robot import PioneerP3DX
            from nav_robot.rl.deploy import run_policy_in_coppelia
            _, sim = connect()
            robot = PioneerP3DX(sim)
            ensure_simulation_running(sim)
            return run_policy_in_coppelia(
                sim, robot, grid, policy, diagonal=diagonal,
                should_stop=lambda: self._stop_requested,
            )

        def done(rep):
            self.btn_run.setEnabled(True)
            if rep.success:
                log.info("GA policy: SUCCES (%d celule, %.2fs)",
                         rep.cells_visited, rep.elapsed_s)
            else:
                log.warning("GA policy: NEINCHEIATA")

        def fail(err):
            self.btn_run.setEnabled(True)
            log.error("Run esuat: %s", err)
            QMessageBox.critical(self, "Eroare", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_save(self) -> None:
        if self.last_ga is None:
            QMessageBox.warning(self, "Nicio politica", "Antreneaza intai GA.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salveaza politica",
                                              "policy_ga.json", "JSON (*.json)")
        if not path:
            return
        self.last_ga.policy().save(path)
        log.info("Politica GA salvata in %s", path)

    def _on_progress(self, gen: int, total: int, best: float, mean: float) -> None:
        self.lbl_status.setText(f"Generatie {gen}/{total} | best={best:.1f} | mean={mean:.1f}")

    def _refresh_plots(self, grid, ga, stats) -> None:
        self.figure.clear()
        ax1 = self.figure.add_subplot(1, 2, 1)
        plot_ga_convergence(stats, ax1)
        ax2 = self.figure.add_subplot(1, 2, 2)
        plot_policy_arrows(grid, ga.policy(), ax2)
        self.canvas.draw_idle()
