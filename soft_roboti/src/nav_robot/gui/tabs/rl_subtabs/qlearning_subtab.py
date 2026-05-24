"""Sub-tab pentru Q-Learning / SARSA - configurare + antrenare + statistici live."""

from __future__ import annotations

import logging

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QFrame, QGroupBox, QLabel, QMessageBox, QPushButton, QRadioButton, QSpinBox,
    QSplitter, QVBoxLayout, QWidget,
)

from nav_robot.gui.worker import run_async
from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.qlearning import QLearningAgent
from nav_robot.rl.sarsa import SARSAAgent
from nav_robot.rl.trainer import evaluate_policy, train_agent
from nav_robot.rl.visualization import (
    plot_policy_arrows, plot_q_heatmap, plot_rewards, plot_success_rate,
)

log = logging.getLogger("gui.rl.ql")


class QLearningSubTab(QWidget):
    """Sub-tab combinat Q-Learning + SARSA (selectabil prin radio)."""

    # Semnale pentru update-uri din thread (postate prin QueuedConnection)
    progress_signal = Signal(int, int, float, float, float)   # ep, total, avg_r, sr, eps

    def __init__(self, map_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab
        self.last_stats = None
        self.last_agent = None
        self._stop_requested = False
        self._thread = None
        self._worker = None
        self._build_ui()
        self.progress_signal.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        left = self._build_config()
        right = self._build_stats()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([360, 700])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(splitter)

    def _build_config(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap)
        v.setSpacing(8)
        v.setContentsMargins(4, 4, 4, 4)

        # Algoritm
        gb_alg = QGroupBox("Algoritm")
        v_alg = QVBoxLayout(gb_alg)
        self.rb_ql = QRadioButton("Q-Learning (off-policy)")
        self.rb_sarsa = QRadioButton("SARSA (on-policy)")
        self.rb_ql.setChecked(True)
        bg = QButtonGroup(self); bg.addButton(self.rb_ql); bg.addButton(self.rb_sarsa)
        v_alg.addWidget(self.rb_ql)
        v_alg.addWidget(self.rb_sarsa)

        # Hiperparametri
        gb_h = QGroupBox("Hiperparametri")
        f = QFormLayout(gb_h)
        self.sp_alpha = QDoubleSpinBox(); self.sp_alpha.setRange(0.01, 1.0); self.sp_alpha.setSingleStep(0.05); self.sp_alpha.setValue(0.2)
        self.sp_gamma = QDoubleSpinBox(); self.sp_gamma.setRange(0.5, 1.0); self.sp_gamma.setSingleStep(0.01); self.sp_gamma.setValue(0.95)
        self.sp_eps = QDoubleSpinBox(); self.sp_eps.setRange(0.0, 1.0); self.sp_eps.setSingleStep(0.05); self.sp_eps.setValue(1.0)
        self.sp_eps_decay = QDoubleSpinBox(); self.sp_eps_decay.setRange(0.9, 1.0); self.sp_eps_decay.setSingleStep(0.001); self.sp_eps_decay.setDecimals(4); self.sp_eps_decay.setValue(0.995)
        self.sp_eps_min = QDoubleSpinBox(); self.sp_eps_min.setRange(0.0, 0.5); self.sp_eps_min.setSingleStep(0.01); self.sp_eps_min.setValue(0.05)
        self.sp_eps_decay.setDecimals(4)
        f.addRow("alpha (rata invatare):", self.sp_alpha)
        f.addRow("gamma (discount):", self.sp_gamma)
        f.addRow("epsilon start:", self.sp_eps)
        f.addRow("epsilon decay:", self.sp_eps_decay)
        f.addRow("epsilon min:", self.sp_eps_min)

        # Antrenare
        gb_t = QGroupBox("Antrenare")
        f2 = QFormLayout(gb_t)
        self.sp_episodes = QSpinBox(); self.sp_episodes.setRange(10, 100_000); self.sp_episodes.setValue(1000)
        self.cb_diagonal = QComboBox(); self.cb_diagonal.addItems(["4 actiuni (N/E/S/V)", "8 actiuni (cu diagonale)"])
        self.cb_random_start = QCheckBox("Start aleator (pentru generalizare)")
        self.cb_in_coppelia = QCheckBox("Antrenare in CoppeliaSim (lent)"); self.cb_in_coppelia.setEnabled(False)   # nu inca
        self.cb_in_coppelia.setToolTip("Disponibil dupa Faza 5d (deploy)")
        self.sp_seed = QSpinBox(); self.sp_seed.setRange(0, 1_000_000); self.sp_seed.setValue(42)
        f2.addRow("Episoade:", self.sp_episodes)
        f2.addRow("Actiuni:", self.cb_diagonal)
        f2.addRow("Seed:", self.sp_seed)
        f2.addRow("", self.cb_random_start)
        f2.addRow("", self.cb_in_coppelia)

        # Butoane
        gb_b = QGroupBox("Actiuni")
        v_b = QVBoxLayout(gb_b)
        self.btn_train = QPushButton("Antreneaza")
        self.btn_stop = QPushButton("Stop")
        self.btn_test_other = QPushButton("Test pe alta harta (seed nou)")
        self.btn_run = QPushButton("Ruleaza in CoppeliaSim")
        self.btn_save = QPushButton("Salveaza politica...")
        self.btn_train.clicked.connect(self._on_train)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_test_other.clicked.connect(self._on_test_other_map)
        self.btn_run.clicked.connect(self._on_run_coppelia)
        self.btn_save.clicked.connect(self._on_save)
        for b in (self.btn_train, self.btn_stop, self.btn_test_other,
                  self.btn_run, self.btn_save):
            v_b.addWidget(b)

        self.lbl_status = QLabel("Astept...")
        self.lbl_status.setStyleSheet("color:#888;")
        self.lbl_status.setWordWrap(True)

        v.addWidget(gb_alg)
        v.addWidget(gb_h)
        v.addWidget(gb_t)
        v.addWidget(gb_b)
        v.addWidget(self.lbl_status)
        v.addStretch(1)
        return wrap

    def _build_stats(self) -> QWidget:
        wrap = QFrame()
        wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap)
        v.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Statistici antrenare")
        title.setStyleSheet("font-weight:bold;")
        v.addWidget(title)

        self.figure = Figure(figsize=(8, 6), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        v.addWidget(self.canvas, stretch=1)
        return wrap

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _selected_algo(self) -> str:
        return "qlearning" if self.rb_ql.isChecked() else "sarsa"

    def _build_agent(self, env):
        algo = self._selected_algo()
        kw = dict(alpha=self.sp_alpha.value(), gamma=self.sp_gamma.value(),
                  eps_start=self.sp_eps.value(), eps_decay=self.sp_eps_decay.value(),
                  eps_min=self.sp_eps_min.value(), seed=self.sp_seed.value())
        if algo == "qlearning":
            return QLearningAgent(env, **kw)
        return SARSAAgent(env, **kw)

    def _build_env(self, grid):
        diagonal = self.cb_diagonal.currentIndex() == 1
        return GridWorldEnv(grid, diagonal=diagonal,
                            random_start=self.cb_random_start.isChecked(),
                            seed=self.sp_seed.value())

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_train(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza o harta in tab-ul Generare harta.")
            return

        env = self._build_env(grid)
        agent = self._build_agent(env)
        n_ep = self.sp_episodes.value()
        algo = self._selected_algo()
        self._stop_requested = False
        self.btn_train.setEnabled(False)
        log.info("[%s] start antrenare: %d episoade.", algo, n_ep)
        self.lbl_status.setText(f"Antrenez {algo} ({n_ep} episoade)...")

        # Captura signal-ul ca local ca sa-l emitem din task
        sig = self.progress_signal

        def task():
            def on_ep(ep, ep_res, stats):
                if (ep + 1) % 25 == 0:
                    window = stats.success_flags[-25:]
                    sr = sum(window) / len(window)
                    avg_r = sum(stats.rewards[-25:]) / len(window)
                    eps = stats.epsilons[-1] if stats.epsilons else 0.0
                    sig.emit(ep + 1, n_ep, float(avg_r), float(sr), float(eps))

            stats = train_agent(agent, env, n_episodes=n_ep,
                                on_episode=on_ep, progress_every=0,
                                should_stop=lambda: self._stop_requested)
            return stats, agent

        def done(result):
            stats, agent = result
            self.btn_train.setEnabled(True)
            self.last_stats = stats
            self.last_agent = agent
            metrics = evaluate_policy(env, agent.policy(), n_episodes=50)
            self.lbl_status.setText(
                f"Gata. Success rate eval={metrics['success_rate']*100:.0f}%, "
                f"mean reward={metrics['mean_reward']:.1f}, "
                f"mean steps={metrics['mean_steps']:.1f}"
            )
            log.info("[%s] eval: success=%.0f%% reward=%.1f steps=%.1f",
                     algo, metrics['success_rate']*100, metrics['mean_reward'],
                     metrics['mean_steps'])
            self._refresh_plots(grid, agent, stats)

        def fail(err):
            self.btn_train.setEnabled(True)
            log.error("Antrenare esuata: %s", err)
            QMessageBox.critical(self, "Eroare antrenare", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_stop(self) -> None:
        self._stop_requested = True
        log.info("Stop antrenare solicitat.")

    def _on_test_other_map(self) -> None:
        if self.last_agent is None:
            QMessageBox.warning(self, "Nicio politica",
                                "Antreneaza intai un agent.")
            return
        # Genereaza o harta cu seed nou si evalueaza politica greedy
        from nav_robot.map import generate_random_map
        cur = self.map_tab.current_grid
        new_seed = (cur.seed or 0) + 1000
        new_grid = generate_random_map(
            width=cur.width, height=cur.height,
            obstacle_ratio=0.25,
            seed=new_seed,
            cell_size=cur.cell_size,
        )
        env_new = GridWorldEnv(new_grid,
                               diagonal=self.cb_diagonal.currentIndex() == 1)
        metrics = evaluate_policy(env_new, self.last_agent.policy(),
                                  n_episodes=50, random_start=True)
        msg = (
            f"Politica antrenata pe seed={cur.seed} testata pe seed={new_seed}\n\n"
            f"  Success rate: {metrics['success_rate']*100:.0f}%\n"
            f"  Mean reward:  {metrics['mean_reward']:.1f}\n"
            f"  Mean steps:   {metrics['mean_steps']:.1f}\n\n"
            f"(Politicile per-celula nu generalizeaza: cand harta se schimba, "
            f"actiunile invatate pentru fiecare celula nu mai au sens.)"
        )
        log.info("Generalizare: success=%.0f%%", metrics['success_rate']*100)
        QMessageBox.information(self, "Test generalizare", msg)

    def _on_run_coppelia(self) -> None:
        if self.last_agent is None:
            QMessageBox.warning(self, "Nicio politica", "Antreneaza intai un agent.")
            return
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta", "Genereaza si trimite o harta intai.")
            return
        policy = self.last_agent.policy()
        log.info("Pornesc rularea politicii in CoppeliaSim.")
        self._stop_requested = False
        self.btn_run.setEnabled(False)

        def task():
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.robot import PioneerP3DX
            from nav_robot.rl.deploy import run_policy_in_coppelia
            _, sim = connect()
            robot = PioneerP3DX(sim)
            ensure_simulation_running(sim)
            return run_policy_in_coppelia(
                sim, robot, grid, policy,
                diagonal=self.cb_diagonal.currentIndex() == 1,
                should_stop=lambda: self._stop_requested,
                on_step=lambda c, a, n: log.info("celula %s --action=%d--> %s", c, a, n),
            )

        def done(rep):
            self.btn_run.setEnabled(True)
            if rep.success:
                log.info("Politica RL: SUCCES (%d celule, %.2fs)",
                         rep.cells_visited, rep.elapsed_s)
            else:
                log.warning("Politica RL: NEINCHEIATA (%d celule, %.2fs)",
                            rep.cells_visited, rep.elapsed_s)

        def fail(err):
            self.btn_run.setEnabled(True)
            log.error("Run RL esuat: %s", err)
            QMessageBox.critical(self, "Eroare", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_save(self) -> None:
        if self.last_agent is None:
            QMessageBox.warning(self, "Nicio politica", "Antreneaza intai un agent.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salveaza politica", "policy.json", "JSON (*.json)",
        )
        if not path:
            return
        self.last_agent.policy().save(path)
        log.info("Politica salvata in %s", path)

    # ------------------------------------------------------------------
    # Slots de update UI
    # ------------------------------------------------------------------
    def _on_progress(self, ep: int, total: int, avg_r: float,
                     sr: float, eps: float) -> None:
        self.lbl_status.setText(
            f"Ep {ep}/{total} | avg_reward={avg_r:.1f} | success={sr*100:.0f}% | eps={eps:.3f}"
        )

    def _refresh_plots(self, grid, agent, stats) -> None:
        self.figure.clear()
        ax1 = self.figure.add_subplot(2, 2, 1)
        plot_rewards(stats.rewards, ax1, rolling=stats.rolling_reward(50))
        ax2 = self.figure.add_subplot(2, 2, 2)
        plot_success_rate(stats.rolling_success(50), ax2)
        ax3 = self.figure.add_subplot(2, 2, 3)
        plot_q_heatmap(grid, agent.q, ax3)
        ax4 = self.figure.add_subplot(2, 2, 4)
        plot_policy_arrows(grid, agent.policy(), ax4)
        self.canvas.draw_idle()
