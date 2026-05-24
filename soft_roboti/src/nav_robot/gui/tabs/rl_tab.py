"""Tab principal Reinforcement Learning - contine sub-tab-uri."""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from nav_robot.gui.tabs.rl_subtabs.compare_subtab import CompareSubTab
from nav_robot.gui.tabs.rl_subtabs.ga_subtab import GASubTab
from nav_robot.gui.tabs.rl_subtabs.qlearning_subtab import QLearningSubTab


class RLTab(QWidget):
    """Tab Reinforcement Learning cu trei sub-tab-uri orizontale:

        - Q-Learning / SARSA : tabular RL
        - Algoritm Genetic   : politici evoluate cu PyGAD (cf. lab 09)
        - Compare            : ruleaza toti 3 si suprapune curbele
    """

    def __init__(self, map_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab
        self._build_ui()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.ql_tab = QLearningSubTab(self.map_tab, self)
        self.ga_tab = GASubTab(self.map_tab, self)
        self.cmp_tab = CompareSubTab(self.map_tab, self)

        self.tabs.addTab(self.ql_tab, "Q-Learning / SARSA")
        self.tabs.addTab(self.ga_tab, "Algoritm Genetic")
        self.tabs.addTab(self.cmp_tab, "Compare")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)
