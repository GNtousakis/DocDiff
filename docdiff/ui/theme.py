"""Look and feel: the "Industry" design system (square hairline frames, blue-grey accent), light and dark."""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QTextCharFormat

from docdiff.diffing import ADDED, CHANGED, REMOVED

FONT_FAMILY = "Segoe UI"

PALETTES = {
    "light": {
        "bg": "#f2f2f3", "surface": "#e9e9ea", "text": "#1d1f20", "divider": "#cdced0",
        "muted": "#707173", "accent": "#5980a6", "accent_hover": "#597ea3", "accent_active": "#416180",
        "on_accent": "#f2f2f3", "banner_bg": "#eef6ff", "banner_border": "#b5d9fd", "banner_fg": "#2c455d",
        "ins_bg": "#d6ebff", "ins_fg": "#1d2d3d", "ins_border": "#94bce3",
        "del_bg": "#e7e7ea", "del_fg": "#5d5d60", "chg_bg": "#fff0a0", "chg_fg": "#6b5400",
        "letter": "#416180", "disabled_bg": "#a9bfd3",
    },
    "dark": {
        "bg": "#161819", "surface": "#1e2022", "text": "#e4e5e7", "divider": "#3a3c3e",
        "muted": "#8e9092", "accent": "#8fb4da", "accent_hover": "#94bce3", "accent_active": "#b5d9fd",
        "on_accent": "#161819", "banner_bg": "#1d2d3d", "banner_border": "#416180", "banner_fg": "#d6ebff",
        "ins_bg": "#2c455d", "ins_fg": "#eef6ff", "ins_border": "#597ea3",
        "del_bg": "#424244", "del_fg": "#d4d4d7", "chg_bg": "#5a4a10", "chg_fg": "#ffe9a0",
        "letter": "#b5d9fd", "disabled_bg": "#4a5a69",
    },
}

_current = "light"


def current() -> str:
    return _current


def set_theme(name: str) -> None:
    global _current
    _current = name if name in PALETTES else "light"


def palette() -> dict[str, str]:
    return PALETTES[_current]


def app_font() -> QFont:
    f = QFont(FONT_FAMILY)
    f.setPixelSize(15)
    f.setStyleHint(QFont.SansSerif)
    return f


def format_for(kind: str) -> QTextCharFormat:
    p = palette()
    fmt = QTextCharFormat()
    if kind == ADDED:
        fmt.setBackground(QColor(p["ins_bg"]))
        fmt.setForeground(QColor(p["ins_fg"]))
    elif kind == REMOVED:
        fmt.setBackground(QColor(p["del_bg"]))
        fmt.setForeground(QColor(p["del_fg"]))
        fmt.setFontStrikeOut(True)
    elif kind == CHANGED:
        fmt.setBackground(QColor(p["chg_bg"]))
        fmt.setForeground(QColor(p["chg_fg"]))
    return fmt


def build_stylesheet(name: str | None = None) -> str:
    """Sizes in px mirror the design prototype (body 15, inputs 14, h3 25, brand 18, counts 11)."""
    p = PALETTES[name or _current]
    head = '"Barlow Condensed", "Fira Sans Condensed", "Segoe UI Semibold", "Segoe UI", sans-serif'
    body = '"Barlow", "Fira Sans", "Segoe UI", sans-serif'
    return f"""
QWidget {{ font-family: {body}; font-size: 15px; color: {p['text']}; }}
QMainWindow, QWidget#central {{ background: {p['bg']}; }}
QFrame#nav {{ border: none; border-bottom: 1px solid {p['divider']}; background: {p['bg']}; }}
QLabel#brand {{ font-family: {head}; font-size: 18px; font-weight: 600; }}
QLabel#brandSub {{ color: {p['muted']}; font-size: 13px; }}
QLabel#count {{ color: {p['muted']}; font-size: 11px; letter-spacing: 1px; }}
QFrame#panel {{ background: transparent; border: none; }}
QLabel#panelTitle {{ font-family: {head}; font-size: 25px; font-weight: 600; }}
QLabel#panelKicker {{ color: {p['letter']}; font-size: 10px; font-weight: 500; letter-spacing: 1px; }}
QLabel#letter {{ border: 1px solid {p['divider']}; color: {p['letter']}; font-family: {head}; font-size: 20px; font-weight: 600; }}
QLabel#regions {{ color: {p['muted']}; font-size: 12px; }}
QLabel#status {{ color: {p['muted']}; font-size: 12px; }}
QLabel#status[level="error"] {{ color: #b42318; }}
QLabel#status[level="warn"] {{ color: #92600a; }}
QFrame#bannerBox {{ background: {p['banner_bg']}; border: 1px solid {p['banner_border']}; border-radius: 0; }}
QLabel#banner {{ background: transparent; color: {p['banner_fg']}; border: none; font-size: 13px; }}
QLabel#bannerTag {{ border: 1px solid {p['accent']}; color: {p['banner_fg']}; padding: 1px 8px; font-family: {head}; font-size: 13px; font-weight: 600; letter-spacing: 1px; }}
QLabel#railHint {{ color: {p['muted']}; font-size: 12px; }}
QLabel#summaryNote {{ color: {p['muted']}; font-size: 12px; }}
QLabel#summaryName {{ font-size: 12px; }}
QLabel#summaryNum {{ font-family: {head}; font-size: 20px; font-weight: 600; }}
QFrame#summaryRow {{ border: none; border-bottom: 1px solid {p['divider']}; }}
QLabel#swatch_removed {{ background: {p['del_bg']}; }}
QLabel#swatch_added {{ background: {p['ins_border']}; }}
QLabel#swatch_changed {{ background: {p['chg_bg']}; }}
QPushButton {{ padding: 8px 12px; border-radius: 0; border: 1px solid {p['divider']}; background: transparent; font-family: {head}; font-size: 14px; font-weight: 600; }}
QPushButton:hover {{ background: {p['divider']}; }}
QPushButton:disabled {{ color: {p['muted']}; }}
QPushButton#primary {{ background: {p['accent']}; color: {p['on_accent']}; border: 1px solid {p['accent']}; font-size: 18px; padding: 14px 10px; }}
QPushButton#primary:hover {{ background: {p['accent_hover']}; }}
QPushButton#primary:pressed {{ background: {p['accent_active']}; }}
QPushButton#primary:disabled {{ background: {p['disabled_bg']}; color: {p['on_accent']}; border: 1px solid {p['disabled_bg']}; }}
QPushButton#ghost {{ border: 1px solid transparent; color: {p['accent']}; padding: 8px 4px; }}
QPushButton#small {{ padding: 2px 8px; font-size: 12px; }}
QPlainTextEdit, QTextEdit {{ border: 1px solid {p['divider']}; border-radius: 0; padding: 10px 14px; background: {p['surface']}; font-family: {body}; font-size: 14px; selection-background-color: {p['accent']}; selection-color: {p['on_accent']}; }}
QPlainTextEdit:focus {{ border-color: {p['accent']}; }}
QLabel#similarity {{ font-family: {head}; font-size: 40px; font-weight: 600; color: {p['letter']}; }}
QLabel#similarityCaption {{ color: {p['muted']}; font-size: 10px; font-weight: 500; letter-spacing: 1px; }}
QLabel#imageView {{ border: 1px solid {p['divider']}; background: {p['surface']}; color: {p['muted']}; font-size: 13px; }}
QPushButton#segment {{ padding: 4px 14px; font-size: 13px; }}
QPushButton#segment:checked {{ background: {p['accent']}; color: {p['on_accent']}; border: 1px solid {p['accent']}; }}
QFrame#thumb {{ border: 1px solid {p['divider']}; border-radius: 0; background: {p['bg']}; }}
"""


STYLESHEET = build_stylesheet("light")
