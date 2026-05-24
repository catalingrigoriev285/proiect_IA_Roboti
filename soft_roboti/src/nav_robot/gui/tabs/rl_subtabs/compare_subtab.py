"""Sub-tab Compare: ruleaza Q-Learning + SARSA + GA pe aceeasi harta si
suprapune curbele de invatare."""

from __future__ import annotations

import logging

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout, QFrame, QGroupBox, QLabel, QMessageBox, QPushButton,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

from nav_robot.gui.worker import run_async
from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.genetic import PolicyGA
from nav_robot.rl.qlearning import QLearningAgent
from nav_robot.rl.sarsa import SARSAAgent
from nav_robot.rl.trainer import evaluate_policy, train_agent

log = logging.getLogger("gui.rl.cmp")


class CompareSubTab(QWidget):
    """Lanseaza secvential cele 3 antrenari pe acelasi env si compara rezultatele."""

    def __init__(self, map_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab
        self._thread = None
        self._worker = None
        self._build_ui()

    def _build_ui(self) -> None:
        left = self._build_config()
        right = self._build_plot()
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0, 0); splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 700])
        layout = QVBoxLayout(self); layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(splitter)

    def _build_config(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap); v.setSpacing(8); v.setContentsMargins(4, 4, 4, 4)

        gb = QGroupBox("Configurare comparativa")
        f = QFormLayout(gb)
        self.sp_ep = QSpinBox(); self.sp_ep.setRange(50, 10_000); self.sp_ep.setValue(500)
        self.sp_pop = QSpinBox(); self.sp_pop.setRange(10, 500); self.sp_pop.setValue(60)
        self.sp_gen = QSpinBox(); self.sp_gen.setRange(10, 1000); self.sp_gen.setValue(60)
        self.sp_seed = QSpinBox(); self.sp_seed.setRange(0, 1_000_000); self.sp_seed.setValue(42)
        f.addRow("Episoade QL/SARSA:", self.sp_ep)
        f.addRow("Pop GA:", self.sp_pop)
        f.addRow("Generatii GA:", self.sp_gen)
        f.addRow("Seed:", self.sp_seed)

        self.btn_run = QPushButton("Compara toti algoritmii")
        self.btn_run.clicked.connect(self._on_run)

        self.lbl = QLabel("Astept ...")
        self.lbl.setStyleSheet("color:#888;"); self.lbl.setWordWrap(True)

        v.addWidget(gb); v.addWidget(self.btn_run); v.addWidget(self.lbl); v.addStretch(1)
        return wrap

    def _build_plot(self) -> QWidget:
        wrap = QFrame(); wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap); v.setContentsMargins(4, 4, 4, 4)
        title = QLabel("Curbele de invatare (rolling success rate)")
        title.setStyleSheet("font-weight:bold;"); v.addWidget(title)
        self.figure = Figure(figsize=(8, 6), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        v.addWidget(self.canvas, stretch=1)
        return wrap

    # ------------------------------------------------------------------
    def _on_run(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza intai o harta in tab-ul Generare harta.")
            return
        self.btn_run.setEnabled(False)
        self.lbl.setText("Antrenez Q-Learning, SARSA si GA ... (poate dura)")
        n_ep = self.sp_ep.value()
        pop = self.sp_pop.value()
        gen = self.sp_gen.value()
        seed = self.sp_seed.value()

        def task():
            results = {}
            for kls, name in [(QLearningAgent, "qlearning"), (SARSAAgent, "sarsa")]:
                env = GridWorldEnv(grid, seed=seed)
                agent = kls(env, alpha=0.2, gamma=0.95, eps_decay=0.995,
                            seed=seed)
                stats = train_agent(agent, env, n_episodes=n_ep,
                                    progress_every=0)
                metrics = evaluate_policy(env, agent.policy(), n_episodes=20)
                results[name] = (stats, metrics)
                log.info("[cmp/%s] eval success=%.0f%% reward=%.1f",
                         name, metrics['success_rate']*100, metrics['mean_reward'])

            # GA
            env = GridWorldEnv(grid, seed=seed)
            ga = PolicyGA(env, pop_size=pop, n_generations=gen,
                          mutation_percent_genes=8.0, seed=seed)
            ga_stats = ga.run()
            ga_metrics = evaluate_policy(env, ga.policy(), n_episodes=20)
            results["genetic"] = (ga_stats, ga_metrics)
            log.info("[cmp/genetic] eval success=%.0f%% reward=%.1f",
                     ga_metrics['success_rate']*100, ga_metrics['mean_reward'])

            return results

        def done(results):
            self.btn_run.setEnabled(True)
            self._show(results)

        def fail(err):
            self.btn_run.setEnabled(True)
            log.error("Compare esuat: %s", err)
            QMessageBox.critical(self, "Eroare", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _show(self, results: dict) -> None:
        ql_stats, ql_m = results["qlearning"]
        sa_stats, sa_m = results["sarsa"]
        ga_stats, ga_m = results["genetic"]

        text = (
            f"<b>Q-Learning</b>: success={ql_m['success_rate']*100:.0f}%, "
            f"reward={ql_m['mean_reward']:.1f}, steps={ql_m['mean_steps']:.1f}<br>"
            f"<b>SARSA</b>: success={sa_m['success_rate']*100:.0f}%, "
            f"reward={sa_m['mean_reward']:.1f}, steps={sa_m['mean_steps']:.1f}<br>"
            f"<b>GA</b>: success={ga_m['success_rate']*100:.0f}%, "
            f"reward={ga_m['mean_reward']:.1f}, steps={ga_m['mean_steps']:.1f}"
        )
        self.lbl.setText(text)

        self.figure.clear()
        ax1 = self.figure.add_subplot(1, 2, 1)
        ax1.plot([s * 100 for s in ql_stats.rolling_success(50)],
                 label="Q-Learning", color="#3498db", linewidth=2)
        ax1.plot([s * 100 for s in sa_stats.rolling_success(50)],
                 label="SARSA", color="#e67e22", linewidth=2)
        ax1.set_xlabel("Episod"); ax1.set_ylabel("Success rate (%)")
        ax1.set_title("Q-Learning vs SARSA: success rate")
        ax1.grid(True, alpha=0.3); ax1.legend(); ax1.set_ylim(0, 105)

        ax2 = self.figure.add_subplot(1, 2, 2)
        ax2.plot(ga_stats.best_fitness, label="GA best", color="#27ae60", linewidth=2)
        ax2.plot(ga_stats.mean_fitness, label="GA mean", color="#aaa", linewidth=1)
        ax2.set_xlabel("Generatie"); ax2.set_ylabel("Fitness")
        ax2.set_title("Algoritm Genetic: convergenta")
        ax2.grid(True, alpha=0.3); ax2.legend()

        self.canvas.draw_idle()
