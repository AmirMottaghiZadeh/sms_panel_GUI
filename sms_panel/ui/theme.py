from __future__ import annotations

from typing import Dict


def _merge_palette(base: Dict[str, str], overrides: Dict[str, str]) -> dict[str, str]:
    merged = dict(base)
    merged.update(overrides)
    return merged


def palette_for(theme_name: str, scheme_name: str) -> dict[str, str]:
    base_light = {
        "bg": "#F4EAE5",
        "bg_alt": "#EAD6CD",
        "surface": "#FFF8F4",
        "surface2": "#F7E7DE",
        "surface3": "#EED5C8",
        "text": "#2F1B33",
        "muted": "#735865",
        "accent": "#4A274F",
        "accent_soft": "#76547D",
        "accent_text": "#FFF6F2",
        "primary_bg": "#4A274F",
        "primary_hover_bg": "#5C3362",
        "primary_pressed_bg": "#381C3D",
        "primary_hover_text": "#FFF6F2",
        "kpi": "#4A274F",
        "ok": "#2A9D8F",
        "warn": "#D88A2A",
        "error": "#C0392B",
        "input_bg": "#FFFDFC",
        "input_border": "#C7A8B5",
        "input_focus": "#4A274F",
        "table_header": "#F1DED3",
        "selection_bg": "#4A274F",
        "selection_text": "#FFF6F2",
        "scroll_bg": "#E8D8D0",
        "scroll_handle": "#B38899",
    }

    base_dark = {
        "bg": "#241726",
        "bg_alt": "#301F34",
        "surface": "#2E1E33",
        "surface2": "#3B2741",
        "surface3": "#4D3555",
        "text": "#F8EBE4",
        "muted": "#D6B3C1",
        "accent": "#F0A07C",
        "accent_soft": "#D990B0",
        "accent_text": "#2B1930",
        "primary_bg": "#4A274F",
        "primary_hover_bg": "#F0A07C",
        "primary_pressed_bg": "#D88561",
        "primary_hover_text": "#2B1930",
        "kpi": "#F0A07C",
        "ok": "#5CC8A1",
        "warn": "#F4C95D",
        "error": "#FF7B7B",
        "input_bg": "#36233A",
        "input_border": "#715177",
        "input_focus": "#F0A07C",
        "table_header": "#4A3151",
        "selection_bg": "#F0A07C",
        "selection_text": "#2B1930",
        "scroll_bg": "#38253D",
        "scroll_handle": "#8B6C92",
    }

    schemes: dict[str, dict[str, dict[str, str]]] = {
        "peach_eggplant": {
            "light": {},
            "dark": {},
        },
        "brown_mustard": {
            "light": {
                "bg": "#F4EDE8",
                "bg_alt": "#EADBCF",
                "surface": "#FFF9F1",
                "surface2": "#F2E1D3",
                "surface3": "#E8CDAF",
                "text": "#2E171B",
                "muted": "#7A5D49",
                "accent": "#4A171E",
                "accent_soft": "#825058",
                "accent_text": "#FFEFC8",
                "primary_bg": "#4A171E",
                "primary_hover_bg": "#E2B144",
                "primary_pressed_bg": "#C3942D",
                "primary_hover_text": "#2F1216",
                "kpi": "#4A171E",
                "ok": "#3B8D5D",
                "warn": "#C58A13",
                "error": "#B73A3A",
                "input_border": "#B69277",
                "input_focus": "#4A171E",
                "selection_bg": "#4A171E",
                "selection_text": "#FFEFC8",
                "scroll_handle": "#A98367",
            },
            "dark": {
                "bg": "#1F1314",
                "bg_alt": "#2C1A1D",
                "surface": "#2B1B1D",
                "surface2": "#3A2629",
                "surface3": "#52383D",
                "text": "#F7E8D3",
                "muted": "#C9A777",
                "accent": "#E2B144",
                "accent_soft": "#DA9258",
                "accent_text": "#2A0E12",
                "primary_bg": "#4A171E",
                "primary_hover_bg": "#E2B144",
                "primary_pressed_bg": "#C4942D",
                "primary_hover_text": "#2A0E12",
                "kpi": "#E2B144",
                "ok": "#5BC08F",
                "warn": "#F0B132",
                "error": "#FF8A7A",
                "input_border": "#86644D",
                "input_focus": "#E2B144",
                "selection_bg": "#E2B144",
                "selection_text": "#2A0E12",
                "scroll_handle": "#8E6C58",
            },
        },
        "orange_black": {
            "light": {
                "bg": "#F7F0E7",
                "bg_alt": "#EED8BE",
                "surface": "#FFF9F2",
                "surface2": "#F6E5D0",
                "surface3": "#ECCCA4",
                "text": "#161B21",
                "muted": "#5A6168",
                "accent": "#161B21",
                "accent_soft": "#3C4652",
                "accent_text": "#F4A950",
                "primary_bg": "#161B21",
                "primary_hover_bg": "#F4A950",
                "primary_pressed_bg": "#DA8D34",
                "primary_hover_text": "#161B21",
                "kpi": "#161B21",
                "ok": "#1E8F6D",
                "warn": "#D47D1E",
                "error": "#B73A3A",
                "input_border": "#A4A7AB",
                "input_focus": "#161B21",
                "selection_bg": "#161B21",
                "selection_text": "#F4A950",
                "scroll_handle": "#8A919A",
            },
            "dark": {
                "bg": "#121519",
                "bg_alt": "#1B2229",
                "surface": "#161B21",
                "surface2": "#252C34",
                "surface3": "#313C48",
                "text": "#FFEED9",
                "muted": "#D6A36A",
                "accent": "#F4A950",
                "accent_soft": "#F4C27E",
                "accent_text": "#161B21",
                "primary_bg": "#161B21",
                "primary_hover_bg": "#F4A950",
                "primary_pressed_bg": "#DA8E38",
                "primary_hover_text": "#161B21",
                "kpi": "#F4A950",
                "ok": "#4CC297",
                "warn": "#F4B25D",
                "error": "#FF8F7A",
                "input_border": "#5F6974",
                "input_focus": "#F4A950",
                "selection_bg": "#F4A950",
                "selection_text": "#161B21",
                "scroll_handle": "#596472",
            },
        },
        "beige_red_gradient": {
            "light": {
                "bg": "#F4EFEA",
                "bg_alt": "#EADCD2",
                "surface": "#FFF9F5",
                "surface2": "#F2E3DB",
                "surface3": "#E8C9BE",
                "text": "#3B161A",
                "muted": "#8A595F",
                "accent": "#7D141D",
                "accent_soft": "#B44D58",
                "accent_text": "#FFF5EE",
                "primary_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D141D, stop:1 #FF1E27)",
                "primary_hover_bg": "#FF1E27",
                "primary_pressed_bg": "#D8141D",
                "primary_hover_text": "#FFF5EE",
                "kpi": "#7D141D",
                "ok": "#2C9A7A",
                "warn": "#C97A2C",
                "error": "#B71724",
                "input_border": "#C29A9F",
                "input_focus": "#7D141D",
                "selection_bg": "#7D141D",
                "selection_text": "#FFF5EE",
                "scroll_handle": "#B78A90",
            },
            "dark": {
                "bg": "#241316",
                "bg_alt": "#361A1E",
                "surface": "#31181C",
                "surface2": "#472126",
                "surface3": "#5F3138",
                "text": "#FCEEE9",
                "muted": "#D9ACA3",
                "accent": "#FF6F76",
                "accent_soft": "#F6989E",
                "accent_text": "#2B1216",
                "primary_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D141D, stop:1 #FF1E27)",
                "primary_hover_bg": "#FF1E27",
                "primary_pressed_bg": "#D8151E",
                "primary_hover_text": "#FCEEE9",
                "kpi": "#FF6F76",
                "ok": "#55C19A",
                "warn": "#F1A649",
                "error": "#FF7D8A",
                "input_border": "#8D5860",
                "input_focus": "#FF6F76",
                "selection_bg": "#FF6F76",
                "selection_text": "#2B1216",
                "scroll_handle": "#95616A",
            },
        },
        "school_navy_gold": {
            "light": {
                "bg": "#EAF2F8",
                "bg_alt": "#D5E4F1",
                "surface": "#FFFFFF",
                "surface2": "#EDF3F9",
                "surface3": "#C7D7EA",
                "text": "#12263A",
                "muted": "#4A6885",
                "accent": "#0E3A67",
                "accent_soft": "#2F5F91",
                "accent_text": "#F8D882",
                "primary_bg": "#0E3A67",
                "primary_hover_bg": "#154C82",
                "primary_pressed_bg": "#0B2F54",
                "primary_hover_text": "#F8D882",
                "kpi": "#0E3A67",
                "ok": "#1F9D7A",
                "warn": "#C98B19",
                "error": "#C45151",
                "input_border": "#9EB8D4",
                "input_focus": "#0E3A67",
                "selection_bg": "#0E3A67",
                "selection_text": "#F8D882",
                "scroll_handle": "#87A6C6",
                "table_header": "#DDE9F4",
            },
            "dark": {
                "bg": "#0F1E2E",
                "bg_alt": "#162A3E",
                "surface": "#17293D",
                "surface2": "#22354D",
                "surface3": "#355273",
                "text": "#ECF4FC",
                "muted": "#B2C7DC",
                "accent": "#F8D882",
                "accent_soft": "#EBC16A",
                "accent_text": "#14263A",
                "primary_bg": "#1E4D80",
                "primary_hover_bg": "#2A639E",
                "primary_pressed_bg": "#19426D",
                "primary_hover_text": "#F8D882",
                "kpi": "#F8D882",
                "ok": "#51C8A6",
                "warn": "#E8BE62",
                "error": "#FF8E8E",
                "input_border": "#4B6C90",
                "input_focus": "#F8D882",
                "selection_bg": "#F8D882",
                "selection_text": "#14263A",
                "scroll_handle": "#5679A0",
                "table_header": "#2A425D",
            },
        },
    }

    mode = "dark" if theme_name == "dark" else "light"
    base = base_dark if mode == "dark" else base_light
    scheme = schemes.get(scheme_name) or schemes["peach_eggplant"]
    return _merge_palette(base, scheme[mode])


def build_stylesheet(
    theme_name: str,
    scheme_name: str,
    font_scale: str = "normal",
    ui_density: str = "comfortable",
) -> str:
    palette = palette_for(theme_name, scheme_name)
    if scheme_name == "school_navy_gold":
        font_stack = '"IRANSansX", "Vazirmatn", "Shabnam", sans-serif'
    else:
        font_stack = '"Vazirmatn", "IRANSansX", "B Mitra", sans-serif'

    scale_map = {"small": 12, "normal": 13, "large": 14}
    base_font_size = scale_map.get(font_scale, 13)
    nav_font_size = base_font_size + 1
    header_font_size = base_font_size + 11
    title_font_size = base_font_size + 7
    subtitle_font_size = base_font_size + 4
    note_font_size = base_font_size + 1

    compact = ui_density == "compact"
    group_padding = 9 if compact else 12
    group_margin_top = 13 if compact else 16
    group_title_padding = 6 if compact else 8
    button_padding_vertical = 6 if compact else 8
    input_padding = 5 if compact else 6
    input_text_padding = 8 if compact else 10
    input_min_height = 36 if compact else 40
    textarea_min_height = 128 if compact else 152

    return f"""
    QMainWindow {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {palette['bg']}, stop:1 {palette['bg_alt']});
    }}
    QWidget {{
        color: {palette['text']};
        font-family: {font_stack};
        font-size: {base_font_size}px;
        selection-background-color: {palette['selection_bg']};
        selection-color: {palette['selection_text']};
    }}
    QToolTip {{
        background: {palette['surface']};
        color: {palette['text']};
        border: 1px solid {palette['surface3']};
        border-radius: 8px;
        padding: {input_padding}px {group_title_padding}px;
    }}
    CardFrame {{
        background: {palette['surface']};
        border: 1px solid {palette['surface3']};
        border-radius: 16px;
    }}
    CardFrame[class="kpi-card"] {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {palette['surface']}, stop:1 {palette['surface2']});
    }}
    QLabel[class="brand-logo"] {{
        background: {palette['surface2']};
        border: 1px solid {palette['surface3']};
        border-radius: 11px;
        padding: 2px;
    }}
    QGroupBox {{
        background: {palette['surface']};
        border: 1px solid {palette['surface3']};
        border-radius: 14px;
        margin-top: {group_margin_top}px;
        padding: {group_padding}px;
        padding-top: {group_padding + 6}px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        right: 18px;
        padding: 0 {group_title_padding}px;
        color: {palette['muted']};
        background: {palette['surface']};
    }}
    QGroupBox#contactsManagerBox::title,
    QGroupBox#sendContactsBox::title {{
        right: 24px;
    }}
    NavButton {{
        text-align: right;
        padding: {group_padding}px 14px;
        border-radius: 12px;
        border: 1px solid transparent;
        background: transparent;
        font-size: {nav_font_size}px;
        font-weight: 600;
    }}
    NavButton:hover {{
        background: {palette['surface2']};
        border-color: {palette['surface3']};
    }}
    NavButton:checked {{
        background: {palette['accent']};
        color: {palette['accent_text']};
        border-color: {palette['accent_soft']};
    }}
    PrimaryButton {{
        background: {palette['primary_bg']};
        color: {palette['accent_text']};
        border: 1px solid {palette['accent_soft']};
        border-radius: 11px;
        padding: {button_padding_vertical}px 14px;
        font-size: {base_font_size}px;
        font-weight: 700;
    }}
    PrimaryButton:hover {{
        background: {palette['primary_hover_bg']};
        color: {palette['primary_hover_text']};
    }}
    PrimaryButton:pressed {{
        background: {palette['primary_pressed_bg']};
    }}
    SecondaryButton {{
        background: {palette['surface2']};
        color: {palette['text']};
        border: 1px solid {palette['input_border']};
        border-radius: 11px;
        padding: {button_padding_vertical}px 12px;
        font-size: {base_font_size}px;
        font-weight: 600;
    }}
    SecondaryButton:hover {{
        background: {palette['surface3']};
        border-color: {palette['accent_soft']};
    }}
    SecondaryButton:pressed {{
        background: {palette['surface2']};
    }}
    PrimaryButton:disabled,
    SecondaryButton:disabled,
    NavButton:disabled {{
        color: {palette['muted']};
        background: {palette['surface2']};
        border-color: {palette['surface3']};
    }}
    QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QDateEdit, QTableWidget, QTreeWidget, QTabWidget::pane {{
        background: {palette['input_bg']};
        border: 1px solid {palette['input_border']};
        border-radius: 10px;
        padding: {input_padding}px;
    }}
    QLineEdit, QComboBox, QSpinBox, QDateEdit {{
        min-height: {input_min_height}px;
    }}
    QLineEdit:hover, QPlainTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDateEdit:hover {{
        border: 1px solid {palette['accent_soft']};
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
        border: 1px solid {palette['input_focus']};
    }}
    QComboBox::drop-down {{
        width: 28px;
        border: 0;
    }}
    QComboBox:on {{
        border: 1px solid {palette['input_focus']};
    }}
    QComboBox QAbstractItemView {{
        background: {palette['surface']};
        color: {palette['text']};
        border: 1px solid {palette['surface3']};
        selection-background-color: {palette['selection_bg']};
        selection-color: {palette['selection_text']};
        outline: 0;
        padding: 4px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: {input_min_height - 4}px;
        padding: 4px 8px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: {palette['surface2']};
    }}
    QPlainTextEdit {{
        padding: {input_text_padding}px;
        min-height: {textarea_min_height}px;
    }}
    QTableWidget, QTreeWidget {{
        alternate-background-color: {palette['surface2']};
        selection-background-color: {palette['selection_bg']};
        selection-color: {palette['selection_text']};
        gridline-color: {palette['surface3']};
    }}
    QHeaderView::section {{
        background: {palette['table_header']};
        color: {palette['text']};
        border: 0;
        padding: {group_title_padding}px;
        font-weight: 700;
    }}
    QTabWidget::pane {{
        border-radius: 12px;
        margin-top: {group_title_padding}px;
    }}
    QTabBar::tab {{
        background: {palette['surface2']};
        padding: {button_padding_vertical}px 14px;
        margin-left: 4px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        border: 1px solid {palette['surface3']};
        border-bottom: 0;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {palette['accent']};
        color: {palette['accent_text']};
        border-color: {palette['accent_soft']};
    }}
    QTabBar::tab:hover:!selected {{
        background: {palette['surface3']};
    }}
    QScrollBar:vertical {{
        background: {palette['scroll_bg']};
        width: 12px;
        margin: 4px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {palette['scroll_handle']};
        min-height: 28px;
        border-radius: 6px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
        border: none;
    }}
    QScrollBar:horizontal {{
        background: {palette['scroll_bg']};
        height: 12px;
        margin: 4px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {palette['scroll_handle']};
        min-width: 28px;
        border-radius: 6px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
        border: none;
    }}
    QLabel[class="fa-header"] {{
        font-family: {font_stack};
        font-size: {header_font_size}px;
        font-weight: 800;
    }}
    QLabel[class="fa-title"] {{
        font-family: {font_stack};
        font-size: {title_font_size}px;
        font-weight: 700;
    }}
    QLabel[class="fa-subtitle"] {{
        font-family: {font_stack};
        font-size: {subtitle_font_size}px;
        font-weight: 700;
    }}
    QLabel[class="fa-note"] {{
        font-family: {font_stack};
        font-size: {note_font_size}px;
    }}
    QLabel[class="muted"] {{
        color: {palette['muted']};
    }}
    QLabel[class="kpi-value"] {{
        font-size: {header_font_size + 10}px;
        font-weight: 800;
        color: {palette['kpi']};
    }}
    StatusBadge {{
        border-radius: 11px;
        padding: {input_padding}px 12px;
        font-weight: 700;
    }}
    StatusBadge[class="badge-ok"] {{
        background: {palette['ok']};
        color: #ffffff;
    }}
    StatusBadge[class="badge-wait"] {{
        background: {palette['warn']};
        color: #2a1900;
    }}
    StatusBadge[class="badge-error"] {{
        background: {palette['error']};
        color: #ffffff;
    }}
    """
