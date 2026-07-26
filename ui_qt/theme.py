"""Tema visual do Extrator SIA/SIH - Qt.

Os valores abaixo (BG_APP, ACCENT, etc.) são o tema ATUALMENTE ativo — são
atualizados em memória por `aplicar_tema()` quando o usuário troca de tema no
seletor da barra superior. Código que faz `from ui_qt import theme` e lê
`theme.ACCENT` sempre pega o valor mais recente, pois é um lookup de atributo
no módulo, não uma cópia. `theme.QSS` é regerado a cada troca; quem chama
`aplicar_tema()` é responsável por reaplicar `QApplication.setStyleSheet(theme.QSS)`.
"""
from ui_qt import temas

# Paletas de sombreamento hierárquico da Tabela Dinâmica: uma escala de passos
# FIXOS (não interpolação contínua) — o último passo é sempre um tom suave,
# então uma hierarquia com muitos níveis não "satura" a tabela inteira de cor
# forte. Profundidades além do último passo repetem o último tom.
# Independe do tema geral do app (o texto da tabela usa cor fixa escura — ver
# pivot_page.py — para garantir contraste mesmo em temas escuros).
PIVOT_PALETTES = {
    "Azul": ["#FFFFFF", "#EEF6FD", "#DCEDFA", "#C7E1F6", "#AFD4F1"],
    "Verde": ["#FFFFFF", "#EDF8F2", "#DBF0E5", "#C5E7D5", "#ACDCC3"],
    "Âmbar": ["#FFFFFF", "#FDF5E7", "#FAEAD0", "#F6DCB4", "#F1CD95"],
    "Ametista": ["#FFFFFF", "#F3EDFB", "#E6DBF7", "#D5C5F1", "#C2ADEA"],
    "Cinza": ["#FFFFFF", "#F2F2F1", "#E5E5E3", "#D6D6D3", "#C6C6C1"],
}


def _construir_qss(t):
    return f"""
QWidget {{
    color: {t['text']};
    font-family: 'Segoe UI';
    font-size: 10pt;
}}

QMainWindow, QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {t['bg_app']};
}}

#TopBar {{
    background-color: {t['bg_card']};
    border-bottom: 1px solid {t['border']};
}}

#TopBarTitle {{
    font-size: 12pt;
    font-weight: 700;
    color: {t['text']};
}}

#TracoAccent {{
    background-color: {t['accent']};
    border-radius: 2px;
}}

QLabel#SectionTitle {{
    font-weight: 700;
    font-size: 10.5pt;
    color: {t['text']};
}}

QLabel#StatusTotal {{
    font-weight: 600;
    color: {t['accent']};
}}

QLabel#Muted {{
    color: {t['text_muted']};
}}

QFrame#Separador {{
    background-color: {t['border']};
    max-height: 1px;
    border: none;
}}

QPushButton {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_strong']};
    border-radius: 6px;
    padding: 6px 14px;
    color: {t['text']};
}}
QPushButton:hover {{
    background-color: {t['accent_soft']};
    border-color: {t['accent']};
}}
QPushButton:disabled {{
    color: #A9AEB5;
    background-color: {t['bg_app']};
    border-color: {t['border']};
}}

QPushButton#Primary {{
    background-color: {t['accent']};
    border: none;
    color: white;
    font-weight: 600;
    padding: 10px 16px;
}}
QPushButton#Primary:hover {{
    background-color: {t['accent_hover']};
}}
QPushButton#Primary:disabled {{
    background-color: #A9CDE6;
}}

QPushButton#IconBtn {{
    padding: 2px 0px;
    font-weight: 600;
}}

QPushButton#Danger {{
    background-color: transparent;
    border: none;
    color: {t['danger']};
}}
QPushButton#Danger:hover {{
    background-color: {t['danger_soft']};
}}

QPushButton#Ghost {{
    background-color: transparent;
    border: none;
    color: {t['text_muted']};
}}
QPushButton#Ghost:hover {{
    background-color: {t['border']};
    color: {t['text']};
}}
QPushButton#Ghost:disabled {{
    background-color: transparent;
    border: none;
    color: #8A8D91;
}}

QFrame#Card {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border']};
    border-radius: 10px;
}}

QFrame#DropZone {{
    background-color: {t['bg_card']};
    border: 2px dashed {t['border_strong']};
    border-radius: 10px;
}}
QFrame#DropZone[dragActive="true"] {{
    border-color: {t['accent']};
    background-color: {t['accent_soft']};
}}

QListWidget, QTreeView, QTableView {{
    background-color: {t['bg_card']};
    alternate-background-color: {t['bg_sidebar']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    gridline-color: {t['border']};
    selection-background-color: {t['accent']};
    selection-color: white;
}}

QHeaderView::section {{
    background-color: {t['bg_sidebar']};
    color: {t['text_muted']};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {t['border']};
    border-right: 1px solid {t['border']};
    font-weight: 600;
}}

QProgressBar {{
    border: 1px solid {t['border']};
    border-radius: 6px;
    background-color: {t['bg_card']};
    text-align: center;
    height: 18px;
}}
QProgressBar::chunk {{
    background-color: {t['accent']};
    border-radius: 5px;
}}

QLineEdit, QComboBox {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_strong']};
    border-radius: 6px;
    padding: 5px 8px;
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {t['accent']};
}}
QComboBox QAbstractItemView {{
    background-color: {t['bg_card']};
    color: {t['text']};
    border: 1px solid {t['border']};
    selection-background-color: {t['accent_soft']};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {t['border_strong']};
    border-radius: 5px;
    min-height: 20px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
}}
QScrollBar::handle:horizontal {{
    background: {t['border_strong']};
    border-radius: 5px;
    min-width: 20px;
}}

QTabWidget::pane {{
    border: 1px solid {t['border']};
    border-radius: 6px;
    background-color: {t['bg_card']};
}}
QTabBar::tab {{
    background-color: {t['bg_app']};
    border: 1px solid {t['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 14px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {t['bg_card']};
    font-weight: 600;
}}

QMenu {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border']};
}}
QMenu::item:selected {{
    background-color: {t['accent_soft']};
}}
"""


def aplicar_tema(nome):
    """Troca o tema ativo: atualiza as constantes deste módulo e regera o QSS.

    Quem chama ainda precisa reaplicar o stylesheet globalmente:
        theme.aplicar_tema(nome)
        QApplication.instance().setStyleSheet(theme.QSS)
    """
    global BG_APP, BG_CARD, BG_SIDEBAR, BORDER, BORDER_STRONG, TEXT, TEXT_MUTED
    global ACCENT, ACCENT_HOVER, ACCENT_SOFT, DANGER, DANGER_SOFT, SUCCESS
    global QSS, TEMA_ATUAL

    t = temas.TEMAS.get(nome, temas.TEMAS[temas.ORDEM_TEMAS[0]])
    BG_APP = t["bg_app"]
    BG_CARD = t["bg_card"]
    BG_SIDEBAR = t["bg_sidebar"]
    BORDER = t["border"]
    BORDER_STRONG = t["border_strong"]
    TEXT = t["text"]
    TEXT_MUTED = t["text_muted"]
    ACCENT = t["accent"]
    ACCENT_HOVER = t["accent_hover"]
    ACCENT_SOFT = t["accent_soft"]
    DANGER = t["danger"]
    DANGER_SOFT = t["danger_soft"]
    SUCCESS = t["success"]
    QSS = _construir_qss(t)
    TEMA_ATUAL = nome
    return QSS


TEMA_ATUAL = temas.ORDEM_TEMAS[0]
aplicar_tema(TEMA_ATUAL)
