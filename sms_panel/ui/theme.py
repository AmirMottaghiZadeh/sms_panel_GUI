from __future__ import annotations


def palette_for(theme_name: str, scheme_name: str) -> dict[str, str]:
    # NOTE: mustard code from the request contained a non-hex character; using E2B144.
    schemes: dict[str, dict[str, dict[str, str]]] = {
        "peach_eggplant": {
            "light": {
                "bg": "#F6ECE8",
                "surface": "#FFF6F2",
                "surface2": "#FBE3D8",
                "text": "#2F1B33",
                "muted": "#77546F",
                "accent": "#4A274F",
                "accent_text": "#F0A07C",
                "primary_bg": "#4A274F",
                "primary_hover_bg": "#F0A07C",
                "primary_hover_text": "#4A274F",
                "kpi": "#4A274F",
                "ok": "#2A9D8F",
                "warn": "#D88A2A",
                "error": "#C0392B",
            },
            "dark": {
                "bg": "#2B1930",
                "surface": "#36213C",
                "surface2": "#44294B",
                "text": "#F9E6DF",
                "muted": "#D9B3A3",
                "accent": "#4A274F",
                "accent_text": "#F0A07C",
                "primary_bg": "#4A274F",
                "primary_hover_bg": "#F0A07C",
                "primary_hover_text": "#4A274F",
                "kpi": "#F0A07C",
                "ok": "#5CC8A1",
                "warn": "#F4C95D",
                "error": "#FF7B7B",
            },
        },
        "brown_mustard": {
            "light": {
                "bg": "#F4EDE8",
                "surface": "#FFF8F1",
                "surface2": "#EEDCCF",
                "text": "#2E171B",
                "muted": "#7A5D49",
                "accent": "#4A171E",
                "accent_text": "#E2B144",
                "primary_bg": "#4A171E",
                "primary_hover_bg": "#E2B144",
                "primary_hover_text": "#351015",
                "kpi": "#4A171E",
                "ok": "#3B8D5D",
                "warn": "#C58A13",
                "error": "#B73A3A",
            },
            "dark": {
                "bg": "#1F1314",
                "surface": "#2B1B1D",
                "surface2": "#3A2629",
                "text": "#F7E8D3",
                "muted": "#C9A777",
                "accent": "#4A171E",
                "accent_text": "#E2B144",
                "primary_bg": "#4A171E",
                "primary_hover_bg": "#E2B144",
                "primary_hover_text": "#2A0E12",
                "kpi": "#E2B144",
                "ok": "#5BC08F",
                "warn": "#F0B132",
                "error": "#FF8A7A",
            },
        },
        "orange_black": {
            "light": {
                "bg": "#F7F0E7",
                "surface": "#FFF9F2",
                "surface2": "#F4DFC5",
                "text": "#161B21",
                "muted": "#5A6168",
                "accent": "#161B21",
                "accent_text": "#F4A950",
                "primary_bg": "#161B21",
                "primary_hover_bg": "#F4A950",
                "primary_hover_text": "#161B21",
                "kpi": "#161B21",
                "ok": "#1E8F6D",
                "warn": "#D47D1E",
                "error": "#B73A3A",
            },
            "dark": {
                "bg": "#121519",
                "surface": "#161B21",
                "surface2": "#252C34",
                "text": "#FFEED9",
                "muted": "#D6A36A",
                "accent": "#161B21",
                "accent_text": "#F4A950",
                "primary_bg": "#161B21",
                "primary_hover_bg": "#F4A950",
                "primary_hover_text": "#161B21",
                "kpi": "#F4A950",
                "ok": "#4CC297",
                "warn": "#F4B25D",
                "error": "#FF8F7A",
            },
        },
        "beige_red_gradient": {
            "light": {
                "bg": "#F4EFEA",
                "surface": "#FFF9F5",
                "surface2": "#F2DFD6",
                "text": "#3B161A",
                "muted": "#8A595F",
                "accent": "#7D141D",
                "accent_text": "#F4EFEA",
                "primary_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D141D, stop:1 #FF1E27)",
                "primary_hover_bg": "#FF1E27",
                "primary_hover_text": "#F4EFEA",
                "kpi": "#7D141D",
                "ok": "#2C9A7A",
                "warn": "#C97A2C",
                "error": "#B71724",
            },
            "dark": {
                "bg": "#241316",
                "surface": "#31181C",
                "surface2": "#472126",
                "text": "#FCEEE9",
                "muted": "#D9ACA3",
                "accent": "#7D141D",
                "accent_text": "#F4EFEA",
                "primary_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7D141D, stop:1 #FF1E27)",
                "primary_hover_bg": "#FF1E27",
                "primary_hover_text": "#FCEEE9",
                "kpi": "#FF6F76",
                "ok": "#55C19A",
                "warn": "#F1A649",
                "error": "#FF7D8A",
            },
        },
    }
    scheme = schemes.get(scheme_name) or schemes["peach_eggplant"]
    return scheme["dark" if theme_name == "dark" else "light"]


def build_stylesheet(theme_name: str, scheme_name: str) -> str:
    palette = palette_for(theme_name, scheme_name)
    return f"""
    QMainWindow {{
        background: {palette['bg']};
    }}
    QWidget {{
        color: {palette['text']};
    }}
    CardFrame {{
        background: {palette['surface']};
        border: 1px solid {palette['surface2']};
        border-radius: 14px;
    }}
    NavButton {{
        text-align: right;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid transparent;
        background: transparent;
        font-size: 14px;
    }}
    NavButton:hover {{
        background: {palette['surface2']};
    }}
    NavButton:checked {{
        background: {palette['accent']};
        color: {palette['accent_text']};
        border-color: {palette['accent_text']};
    }}
    PrimaryButton {{
        background: {palette['primary_bg']};
        color: {palette['accent_text']};
        border: 1px solid {palette['accent_text']};
        border-radius: 10px;
        padding: 8px 12px;
        font-weight: 600;
    }}
    PrimaryButton:hover {{
        background: {palette['primary_hover_bg']};
        color: {palette['primary_hover_text']};
    }}
    SecondaryButton {{
        background: {palette['surface2']};
        color: {palette['text']};
        border: 1px solid {palette['muted']};
        border-radius: 10px;
        padding: 8px 12px;
    }}
    SecondaryButton:hover {{
        border-color: {palette['accent']};
    }}
    QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QTableWidget, QTabWidget::pane {{
        background: {palette['surface']};
        border: 1px solid {palette['muted']};
        border-radius: 10px;
        padding: 6px;
    }}
    QComboBox QAbstractItemView {{
        background: {palette['surface']};
        color: {palette['text']};
        border: 1px solid {palette['muted']};
        selection-background-color: {palette['accent']};
        selection-color: {palette['accent_text']};
        outline: 0;
    }}
    QPlainTextEdit {{
        padding: 10px;
    }}
    QTableWidget {{
        alternate-background-color: {palette['surface2']};
        selection-background-color: {palette['accent']};
        selection-color: {palette['accent_text']};
        gridline-color: {palette['surface2']};
    }}
    QHeaderView::section {{
        background: {palette['surface2']};
        border: 0;
        padding: 6px;
    }}
    QTabBar::tab {{
        background: {palette['surface2']};
        padding: 8px 12px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    QTabBar::tab:selected {{
        background: {palette['accent']};
        color: {palette['accent_text']};
    }}
    QLabel[class="fa-header"] {{
        font-family: "B Mitra", "Mitra", sans-serif;
        font-size: 24px;
        font-weight: 700;
    }}
    QLabel[class="fa-title"] {{
        font-family: "B Mitra", "Mitra", sans-serif;
        font-size: 20px;
        font-weight: 700;
    }}
    QLabel[class="fa-subtitle"] {{
        font-family: "B Mitra", "Mitra", sans-serif;
        font-size: 18px;
        font-weight: 600;
    }}
    QLabel[class="fa-note"] {{
        font-family: "B Mitra", "Mitra", sans-serif;
        font-size: 15px;
    }}
    QLabel[class="muted"] {{
        color: {palette['muted']};
    }}
    QLabel[class="kpi-value"] {{
        font-size: 32px;
        font-weight: 700;
        color: {palette['kpi']};
    }}
    StatusBadge {{
        border-radius: 10px;
        padding: 6px 10px;
        font-weight: 600;
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
