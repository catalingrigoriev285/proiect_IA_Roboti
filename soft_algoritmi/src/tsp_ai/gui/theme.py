"""Theme system for the GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from PySide2.QtWidgets import QApplication


@dataclass(frozen=True)
class ThemePalette:
    """Color palette for the GUI."""

    background: str
    surface: str
    surface_alt: str
    accent: str
    accent2: str
    success: str
    warning: str
    danger: str
    text: str
    text_muted: str
    border: str


DARK_PALETTE = ThemePalette(
    background="#0F172A",
    surface="#111827",
    surface_alt="#1F2937",
    accent="#38BDF8",
    accent2="#A78BFA",
    success="#22C55E",
    warning="#F59E0B",
    danger="#EF4444",
    text="#E5E7EB",
    text_muted="#94A3B8",
    border="#334155",
)

LIGHT_PALETTE = ThemePalette(
    background="#F8FAFC",
    surface="#FFFFFF",
    surface_alt="#F1F5F9",
    accent="#0284C7",
    accent2="#7C3AED",
    success="#16A34A",
    warning="#D97706",
    danger="#DC2626",
    text="#0F172A",
    text_muted="#475569",
    border="#CBD5F5",
)


def build_stylesheet(palette: ThemePalette) -> str:
    """Build the QSS stylesheet for the given palette.

    Args:
        palette: ThemePalette instance.

    Returns:
        QSS stylesheet string.
    """
    return f"""
    * {{
        font-family: "Segoe UI";
        color: {palette.text};
    }}
    QWidget {{
        background-color: {palette.background};
    }}
    QFrame#Card {{
        background-color: {palette.surface};
        border: 1px solid {palette.border};
        border-radius: 12px;
    }}
    QFrame#Sidebar {{
        background-color: {palette.surface};
        border-right: 1px solid {palette.border};
    }}
    QLabel#Title {{
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel#SectionHeader {{
        font-size: 14px;
        font-weight: 600;
        color: {palette.text_muted};
    }}
    QPushButton {{
        background-color: {palette.surface_alt};
        border: 1px solid {palette.border};
        padding: 8px 12px;
        border-radius: 8px;
    }}
    QPushButton:hover {{
        border-color: {palette.accent};
    }}
    QPushButton#Accent {{
        background-color: {palette.accent};
        color: #0F172A;
        font-weight: 600;
    }}
    QPushButton#Accent:hover {{
        background-color: {palette.accent2};
        color: #0F172A;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
        background-color: {palette.surface_alt};
        border: 1px solid {palette.border};
        border-radius: 6px;
        padding: 4px 6px;
    }}
    QTableWidget {{
        background-color: {palette.surface};
        alternate-background-color: {palette.surface_alt};
        gridline-color: {palette.border};
        border: 1px solid {palette.border};
        border-radius: 10px;
    }}
    QTableWidget::item {{
        background-color: transparent;
        color: {palette.text};
        padding: 4px 6px;
    }}
    QTableWidget::item:selected {{
        background-color: {palette.accent2};
        color: #0F172A;
    }}
    QHeaderView::section {{
        background-color: {palette.surface_alt};
        color: {palette.text};
        padding: 6px 8px;
        border: 1px solid {palette.border};
    }}
    QTableCornerButton::section {{
        background-color: {palette.surface_alt};
        border: 1px solid {palette.border};
    }}
    QProgressBar {{
        border: 1px solid {palette.border};
        border-radius: 6px;
        text-align: center;
        background-color: {palette.surface_alt};
    }}
    QProgressBar::chunk {{
        background-color: {palette.accent};
        border-radius: 6px;
    }}
    QListWidget {{
        background-color: {palette.surface};
        border: 1px solid {palette.border};
        border-radius: 10px;
    }}
    QTabBar::tab {{
        background: {palette.surface};
        border: 1px solid {palette.border};
        padding: 6px 10px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QTabBar::tab:selected {{
        background: {palette.surface_alt};
        border-bottom: 2px solid {palette.accent};
    }}
    """


def apply_theme(app: QApplication, dark: bool = True) -> None:
    """Apply the GUI theme to the QApplication.

    Args:
        app: QApplication instance.
        dark: Whether to apply the dark theme.
    """
    palette = DARK_PALETTE if dark else LIGHT_PALETTE
    app.setStyleSheet(build_stylesheet(palette))
    app.setProperty("theme", "dark" if dark else "light")
