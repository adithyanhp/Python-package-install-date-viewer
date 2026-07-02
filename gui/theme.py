"""
gui/theme.py

Central place for the application's dark-violet color palette and
fonts, plus a CustomTkinter JSON theme file writer so the whole app
(including built-in widgets) picks up consistent colors.
"""

from __future__ import annotations

import json
from pathlib import Path

# ----------------------------------------------------------------------
# Palette
# ----------------------------------------------------------------------
BG_PRIMARY = "#15111F"
BG_SECONDARY = "#1E1830"
BG_SIDEBAR = "#1A1526"
BG_CARD = "#241C38"
BG_HOVER = "#2E2445"

ACCENT = "#8B5CF6"
ACCENT_HOVER = "#7C3AED"
ACCENT_DARK = "#6C3FC5"

TEXT_PRIMARY = "#F1EDFB"
TEXT_SECONDARY = "#A99FC4"
TEXT_MUTED = "#6E6486"

SUCCESS = "#4ADE80"
WARNING = "#FBBF24"
DANGER = "#F87171"

BORDER = "#332A4D"

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

THEME_DIR = Path(__file__).resolve().parent.parent / "assets" / "themes"
THEME_FILE = THEME_DIR / "dark_violet.json"


def _ctk_theme_dict() -> dict:
    """Build a CustomTkinter-compatible theme dictionary."""
    return {
        "CTk": {"fg_color": [BG_PRIMARY, BG_PRIMARY]},
        "CTkToplevel": {"fg_color": [BG_PRIMARY, BG_PRIMARY]},
        "CTkFrame": {
            "corner_radius": 10,
            "border_width": 0,
            "fg_color": [BG_CARD, BG_CARD],
            "top_fg_color": [BG_SECONDARY, BG_SECONDARY],
            "border_color": [BORDER, BORDER],
        },
        "CTkButton": {
            "corner_radius": 8,
            "border_width": 0,
            "fg_color": [ACCENT_DARK, ACCENT_DARK],
            "hover_color": [ACCENT_HOVER, ACCENT_HOVER],
            "border_color": [BORDER, BORDER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkLabel": {
            "corner_radius": 0,
            "border_width": 0,
            "fg_color": "transparent",
            "border_color": [BORDER, BORDER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        },
        "CTkEntry": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "border_color": [BORDER, BORDER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "placeholder_text_color": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkCheckBox": {
            "corner_radius": 4,
            "border_width": 2,
            "fg_color": [ACCENT_DARK, ACCENT_DARK],
            "border_color": [BORDER, BORDER],
            "hover_color": [ACCENT_HOVER, ACCENT_HOVER],
            "checkmark_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkSwitch": {
            "corner_radius": 1000,
            "border_width": 3,
            "button_length": 0,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "progress_color": [ACCENT_DARK, ACCENT_DARK],
            "button_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "button_hover_color": [TEXT_SECONDARY, TEXT_SECONDARY],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkScrollbar": {
            "corner_radius": 1000,
            "border_spacing": 4,
            "fg_color": "transparent",
            "button_color": [BORDER, BORDER],
            "button_hover_color": [ACCENT_DARK, ACCENT_DARK],
        },
        "CTkProgressBar": {
            "corner_radius": 1000,
            "border_width": 0,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "progress_color": [ACCENT_DARK, ACCENT_DARK],
            "border_color": [BORDER, BORDER],
        },
        "CTkSlider": {
            "corner_radius": 1000,
            "button_corner_radius": 1000,
            "border_width": 6,
            "button_length": 0,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "progress_color": [ACCENT_DARK, ACCENT_DARK],
            "button_color": [ACCENT, ACCENT],
            "button_hover_color": [ACCENT_HOVER, ACCENT_HOVER],
        },
        "CTkOptionMenu": {
            "corner_radius": 8,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "button_color": [ACCENT_DARK, ACCENT_DARK],
            "button_hover_color": [ACCENT_HOVER, ACCENT_HOVER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkComboBox": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "border_color": [BORDER, BORDER],
            "button_color": [ACCENT_DARK, ACCENT_DARK],
            "button_hover_color": [ACCENT_HOVER, ACCENT_HOVER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkScrollableFrame": {"label_fg_color": [BG_SECONDARY, BG_SECONDARY]},
        "CTkSegmentedButton": {
            "corner_radius": 8,
            "border_width": 2,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "selected_color": [ACCENT_DARK, ACCENT_DARK],
            "selected_hover_color": [ACCENT_HOVER, ACCENT_HOVER],
            "unselected_color": [BG_SECONDARY, BG_SECONDARY],
            "unselected_hover_color": [BG_HOVER, BG_HOVER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        },
        "CTkTextbox": {
            "corner_radius": 8,
            "border_width": 1,
            "fg_color": [BG_SECONDARY, BG_SECONDARY],
            "border_color": [BORDER, BORDER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
            "scrollbar_button_color": [BORDER, BORDER],
            "scrollbar_button_hover_color": [ACCENT_DARK, ACCENT_DARK],
        },
        "DropdownMenu": {
            "fg_color": [BG_CARD, BG_CARD],
            "hover_color": [BG_HOVER, BG_HOVER],
            "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        },
        "CTkFont": {
            "macOS": {"family": "SF Display", "size": 13, "weight": "normal"},
            "Windows": {"family": FONT_FAMILY, "size": 13, "weight": "normal"},
            "Linux": {"family": "Roboto", "size": 13, "weight": "normal"},
        },
    }


def write_theme_file() -> Path:
    """Write the CTk theme JSON to disk (idempotent) and return its path."""
    THEME_DIR.mkdir(parents=True, exist_ok=True)
    THEME_FILE.write_text(json.dumps(_ctk_theme_dict(), indent=2), encoding="utf-8")
    return THEME_FILE
