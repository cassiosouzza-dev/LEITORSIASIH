"""Janela principal: uma única janela com navegação interna (sem popups soltos)."""
import json
import logging
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QComboBox, QApplication,
)

from ui_qt import theme, temas


def resource_path(relative_path):
    """Caminho de recurso somente-leitura empacotado (ex.: ícone)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def dados_path(relative_path):
    """Caminho de arquivo de dados do usuário (config, histórico, templates).

    Em build via PyInstaller --onefile, sys._MEIPASS é uma pasta temporária
    recriada e apagada a cada execução — gravar ali faz o histórico/tema
    "sumirem" ao reabrir o app. Por isso aqui usamos a pasta do .exe (ou do
    projeto, rodando a partir do código-fonte), que persiste entre execuções.
    """
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


CONFIG_PATH = dados_path("ui_config.json")


def _carregar_tema_salvo():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            nome = json.load(f).get("tema")
            if nome in temas.TEMAS:
                return nome
    except FileNotFoundError:
        pass
    except Exception:
        logging.exception("Falha ao carregar tema salvo de %s", CONFIG_PATH)
    return temas.ORDEM_TEMAS[0]


def _salvar_tema(nome):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"tema": nome}, f, ensure_ascii=False)
    except Exception:
        logging.exception("Falha ao salvar tema em %s", CONFIG_PATH)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        tema_inicial = _carregar_tema_salvo()
        theme.aplicar_tema(tema_inicial)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme.QSS)

        self.setWindowTitle("Extrator SIA/SIH")
        self.resize(1200, 720)

        icon_path = resource_path("extrator_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Barra superior (título da página + botão Voltar) ---
        self.top_bar = QWidget()
        self.top_bar.setObjectName("TopBar")
        self.top_bar.setFixedHeight(56)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(14)

        self.btn_voltar = QPushButton("←  Voltar")
        self.btn_voltar.setObjectName("Ghost")
        self.btn_voltar.setCursor(Qt.PointingHandCursor)
        self.btn_voltar.clicked.connect(self.voltar)
        self.btn_voltar.setEnabled(False)
        top_layout.addWidget(self.btn_voltar)

        self.tracinho_titulo = QFrame()
        self.tracinho_titulo.setObjectName("TracoAccent")
        self.tracinho_titulo.setFixedSize(4, 22)
        top_layout.addWidget(self.tracinho_titulo)

        self.lbl_titulo = QLabel("Upload de Arquivos")
        self.lbl_titulo.setObjectName("TopBarTitle")
        top_layout.addWidget(self.lbl_titulo)
        top_layout.addStretch(1)

        top_layout.addWidget(QLabel("Tema:"))
        self.cb_tema_app = QComboBox()
        self.cb_tema_app.addItems(temas.ORDEM_TEMAS)
        self.cb_tema_app.setCurrentText(theme.TEMA_ATUAL)
        self.cb_tema_app.setFixedWidth(130)
        self.cb_tema_app.currentTextChanged.connect(self._mudar_tema_app)
        top_layout.addWidget(self.cb_tema_app)

        root.addWidget(self.top_bar)

        # --- Área de conteúdo (páginas) ---
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.history = []  # lista de (widget, titulo)

    # --- TEMA ---
    def _mudar_tema_app(self, nome):
        theme.aplicar_tema(nome)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme.QSS)
        _salvar_tema(nome)

    # --- NAVEGAÇÃO ---
    def set_home(self, widget, titulo):
        """Define a página inicial (Upload). Chamado uma única vez."""
        self.stack.addWidget(widget)
        self.history = [(widget, titulo)]
        self.stack.setCurrentWidget(widget)
        self._atualizar_topbar()

    def push_page(self, widget, titulo):
        """Abre uma nova página, empilhando sobre a atual (permite voltar)."""
        self.stack.addWidget(widget)
        self.history.append((widget, titulo))
        self.stack.setCurrentWidget(widget)
        self._atualizar_topbar()

    def voltar(self):
        if len(self.history) <= 1:
            return
        widget, _ = self.history.pop()
        self.stack.removeWidget(widget)
        widget.deleteLater()
        prev_widget, _ = self.history[-1]
        self.stack.setCurrentWidget(prev_widget)
        self._atualizar_topbar()

    def reset_to_home(self):
        """Descarta todas as páginas acima da Home (usado ao reprocessar novos arquivos)."""
        while len(self.history) > 1:
            widget, _ = self.history.pop()
            self.stack.removeWidget(widget)
            widget.deleteLater()
        home_widget, _ = self.history[0]
        self.stack.setCurrentWidget(home_widget)
        self._atualizar_topbar()

    def _atualizar_topbar(self):
        widget, titulo = self.history[-1]
        self.lbl_titulo.setText(titulo)
        self.btn_voltar.setEnabled(len(self.history) > 1)
