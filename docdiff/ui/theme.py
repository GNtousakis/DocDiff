"""Look and feel: Segoe UI, generous spacing, large buttons."""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QTextCharFormat

from docdiff.diffing import ADDED, CHANGED, REMOVED

FONT_FAMILY = "Segoe UI"

ADDED_BG, ADDED_FG = QColor("#c8f0cf"), QColor("#14612a")
REMOVED_BG, REMOVED_FG = QColor("#ffd0d0"), QColor("#9b1c1c")
CHANGED_BG, CHANGED_FG = QColor("#fff0a0"), QColor("#6b5400")


def app_font() -> QFont:
    f = QFont(FONT_FAMILY, 10)
    f.setStyleHint(QFont.SansSerif)
    return f


def format_for(kind: str) -> QTextCharFormat:
    fmt = QTextCharFormat()
    if kind == ADDED:
        fmt.setBackground(ADDED_BG)
        fmt.setForeground(ADDED_FG)
        fmt.setFontUnderline(True)
    elif kind == REMOVED:
        fmt.setBackground(REMOVED_BG)
        fmt.setForeground(REMOVED_FG)
        fmt.setFontStrikeOut(True)
    elif kind == CHANGED:
        fmt.setBackground(CHANGED_BG)
        fmt.setForeground(CHANGED_FG)
    return fmt


STYLESHEET = """
QWidget { font-family: "Segoe UI", sans-serif; font-size: 10pt; }
QMainWindow, QWidget#central { background: #f4f5f7; }
QFrame#panel { background: white; border: 1px solid #d9dce1; border-radius: 10px; }
QLabel#panelTitle { font-size: 14pt; font-weight: 600; color: #1f2933; }
QLabel#status { color: #52606d; }
QLabel#status[level="error"] { color: #b42318; }
QLabel#status[level="warn"] { color: #92600a; }
QLabel#banner { background: #fff4d6; color: #5c3d00; border: 1px solid #f0c36d; border-radius: 8px; padding: 10px 14px; }
QLabel#summary { font-size: 13pt; font-weight: 600; color: #1f2933; }
QPushButton { min-height: 40px; padding: 4px 16px; border-radius: 8px; border: 1px solid #c4c9d0; background: white; }
QPushButton:hover { background: #eef1f5; }
QPushButton:disabled { color: #9aa5b1; background: #f1f3f5; }
QPushButton#primary { background: #1f6feb; color: white; border: none; font-size: 15pt; font-weight: 600; min-height: 64px; min-width: 150px; }
QPushButton#primary:hover { background: #1a5fcb; }
QPushButton#primary:disabled { background: #b8c4d6; color: #eef1f5; }
QPushButton#small { min-height: 24px; padding: 0 8px; font-size: 9pt; }
QPlainTextEdit, QTextEdit { border: 1px solid #d9dce1; border-radius: 8px; padding: 8px; background: white; font-size: 11pt; }
QFrame#thumb { border: 1px solid #d9dce1; border-radius: 6px; background: #fafbfc; }
"""
