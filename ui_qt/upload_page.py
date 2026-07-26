"""Tela 1: Upload de Arquivos (drag&drop, seleção manual, recentes, processamento)."""
import json
import os

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog,
    QProgressBar, QMessageBox, QSizePolicy,
)

from ui_qt.main_window import resource_path
from ui_qt.worker import iniciar_extracao

HISTORICO_PATH = resource_path("recentes.json")
SERIE_HISTORICA_PATH = resource_path("Serie_historica.xlsx")
MAX_HISTORICO = 30


class DropZone(QFrame):
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(260)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        pdfs = [p for p in paths if p.lower().endswith(".pdf")]
        if pdfs:
            self.filesDropped.emit(pdfs)


class UploadPage(QWidget):
    def __init__(self, on_processed, on_open_historico):
        super().__init__()
        self.on_processed = on_processed
        self.on_open_historico = on_open_historico
        self.files = []
        self._thread = None
        self._worker = None

        root = QHBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        # ================= COLUNA ESQUERDA =================
        left = QVBoxLayout()
        left.setSpacing(10)
        root.addLayout(left, 1)

        titulo = QLabel("Upload de Arquivos")
        titulo.setStyleSheet("font-size: 18pt; font-weight: 700;")
        left.addWidget(titulo)

        subtitulo = QLabel("Arraste arquivos PDF ou selecione manualmente")
        subtitulo.setObjectName("Muted")
        left.addWidget(subtitulo)

        self.drop_zone = DropZone()
        self.drop_zone.filesDropped.connect(self._adicionar_arquivos)
        drop_layout = QVBoxLayout(self.drop_zone)
        self.lbl_drop_placeholder = QLabel("Solte os arquivos aqui")
        self.lbl_drop_placeholder.setAlignment(Qt.AlignCenter)
        self.lbl_drop_placeholder.setObjectName("Muted")
        self.lbl_drop_placeholder.setStyleSheet("border: none;")
        drop_layout.addWidget(self.lbl_drop_placeholder)

        self.lista_arquivos = QListWidget()
        self.lista_arquivos.setFrameShape(QFrame.NoFrame)
        self.lista_arquivos.setVisible(False)
        drop_layout.addWidget(self.lista_arquivos)

        left.addWidget(self.drop_zone, 1)

        btn_box = QHBoxLayout()
        self.btn_selecionar = QPushButton("Selecionar Arquivos")
        self.btn_selecionar.clicked.connect(self._selecionar_manual)
        btn_box.addWidget(self.btn_selecionar)
        btn_box.addStretch(1)
        self.btn_limpar = QPushButton("Limpar Tudo")
        self.btn_limpar.setObjectName("Danger")
        self.btn_limpar.clicked.connect(self._limpar_tudo)
        btn_box.addWidget(self.btn_limpar)
        left.addLayout(btn_box)

        self.btn_run = QPushButton("INICIAR PROCESSAMENTO")
        self.btn_run.setObjectName("Primary")
        self.btn_run.setMinimumHeight(48)
        self.btn_run.clicked.connect(self._iniciar_processamento)
        left.addWidget(self.btn_run)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        left.addWidget(self.progress)

        self.lbl_status = QLabel("Aguardando...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setObjectName("Muted")
        left.addWidget(self.lbl_status)

        # ================= COLUNA DIREITA (RECENTES) =================
        right = QVBoxLayout()
        right.setSpacing(10)
        right_widget = QFrame()
        right_widget.setObjectName("Card")
        right_widget.setFixedWidth(340)
        right_inner = QVBoxLayout(right_widget)
        root.addWidget(right_widget)

        head = QHBoxLayout()
        lbl_recentes = QLabel("Recentes")
        lbl_recentes.setStyleSheet("font-size: 12pt; font-weight: 700;")
        head.addWidget(lbl_recentes)
        head.addStretch(1)
        btn_limpar_hist = QPushButton("Limpar")
        btn_limpar_hist.setObjectName("Ghost")
        btn_limpar_hist.clicked.connect(self._limpar_historico)
        head.addWidget(btn_limpar_hist)
        right_inner.addLayout(head)

        self.lista_recentes = QListWidget()
        self.lista_recentes.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.lista_recentes.itemDoubleClicked.connect(self._duplo_clique_recente)
        right_inner.addWidget(self.lista_recentes, 1)

        self.btn_reutilizar = QPushButton("Reutilizar Selecionados")
        self.btn_reutilizar.clicked.connect(self._reutilizar_selecionados)
        right_inner.addWidget(self.btn_reutilizar)

        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        right_inner.addWidget(linha)

        self.btn_historico = QPushButton("Abrir Série Histórica")
        self.btn_historico.clicked.connect(self._abrir_serie_historica)
        right_inner.addWidget(self.btn_historico)

        self._carregar_painel_recentes()

    # ---------------- ARQUIVOS ATUAIS ----------------
    def _adicionar_arquivos(self, paths):
        for p in paths:
            if p not in self.files:
                self.files.append(p)
        self._atualizar_lista_arquivos()

    def _selecionar_manual(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF (*.pdf)")
        if fs:
            self._adicionar_arquivos(fs)

    def _remover_arquivo(self, path):
        if path in self.files:
            self.files.remove(path)
        self._atualizar_lista_arquivos()

    def _limpar_tudo(self):
        self.files = []
        self._atualizar_lista_arquivos()

    def _atualizar_lista_arquivos(self):
        self.lista_arquivos.clear()
        tem_arquivos = bool(self.files)
        self.lbl_drop_placeholder.setVisible(not tem_arquivos)
        self.lista_arquivos.setVisible(tem_arquivos)

        for f in self.files:
            nome = os.path.basename(f)
            if len(nome) > 70:
                nome = nome[:65] + "..."
            item = QListWidgetItem(self.lista_arquivos)
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 2, 4, 2)
            row_layout.addWidget(QLabel(nome), 1)
            btn_del = QPushButton("✕")
            btn_del.setObjectName("Ghost")
            btn_del.setStyleSheet("padding: 2px 0px;")
            btn_del.setFixedWidth(28)
            btn_del.clicked.connect(lambda checked=False, path=f: self._remover_arquivo(path))
            row_layout.addWidget(btn_del)
            item.setSizeHint(row.sizeHint())
            self.lista_arquivos.addItem(item)
            self.lista_arquivos.setItemWidget(item, row)

    # ---------------- RECENTES ----------------
    def _carregar_historico(self):
        if os.path.exists(HISTORICO_PATH):
            try:
                with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _carregar_painel_recentes(self):
        self.lista_recentes.clear()
        historico = [p for p in self._carregar_historico() if os.path.exists(p)]
        if not historico:
            item = QListWidgetItem("Nenhum histórico.")
            item.setFlags(Qt.NoItemFlags)
            self.lista_recentes.addItem(item)
            return
        for path in historico:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)
            self.lista_recentes.addItem(item)

    def _reutilizar_selecionados(self):
        selecionados = self.lista_recentes.selectedItems()
        paths = [it.data(Qt.UserRole) for it in selecionados if it.data(Qt.UserRole)]
        if not paths:
            QMessageBox.information(self, "Info", "Selecione arquivos na lista de recentes.")
            return
        self._adicionar_arquivos(paths)
        self.lista_recentes.clearSelection()

    def _duplo_clique_recente(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self._adicionar_arquivos([path])

    def _limpar_historico(self):
        resposta = QMessageBox.question(
            self, "Confirmar", "Deseja apagar todo o histórico de arquivos recentes?"
        )
        if resposta != QMessageBox.Yes:
            return
        if os.path.exists(HISTORICO_PATH):
            try:
                os.remove(HISTORICO_PATH)
            except Exception:
                pass
        self._carregar_painel_recentes()

    def _salvar_historico(self):
        atual = self._carregar_historico()
        novos = [f for f in self.files if f not in atual]
        lista_final = (novos + atual)[:MAX_HISTORICO]
        try:
            with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False)
        except Exception:
            pass

    # ---------------- SÉRIE HISTÓRICA ----------------
    def _abrir_serie_historica(self):
        if not os.path.exists(SERIE_HISTORICA_PATH):
            QMessageBox.warning(
                self, "Não encontrado",
                f"O arquivo '{os.path.basename(SERIE_HISTORICA_PATH)}' ainda não existe.\n\n"
                "Você precisa processar arquivos e clicar em 'Adicionar ao Histórico' na tela de "
                "resultados para criá-lo."
            )
            return
        try:
            df_hist = pd.read_excel(SERIE_HISTORICA_PATH)
            if "Valor" in df_hist.columns:
                df_hist["Valor"] = pd.to_numeric(df_hist["Valor"], errors="coerce").fillna(0.0)
            self.on_open_historico(df_hist)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao abrir Série Histórica:\n{e}")

    # ---------------- PROCESSAMENTO ----------------
    def _iniciar_processamento(self):
        if not self.files:
            QMessageBox.warning(self, "!", "Adicione arquivos para processar.")
            return

        self._salvar_historico()
        self.btn_run.setEnabled(False)
        self.btn_run.setText("PROCESSANDO...")
        self.progress.setValue(0)
        self.lbl_status.setText("Iniciando...")

        self._thread, self._worker = iniciar_extracao(list(self.files))
        # Conecta a métodos vinculados (bound methods) desta QWidget: o Qt detecta
        # que ela vive na thread principal e despacha as chamadas em fila
        # automaticamente, evitando mexer na UI a partir da thread de trabalho.
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def _on_progress(self, texto, valor):
        self.lbl_status.setText(texto)
        self.progress.setValue(int(valor * 100))

    def _on_finished(self, df):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("INICIAR PROCESSAMENTO")
        self._carregar_painel_recentes()

        if df is None or df.empty:
            self.progress.setValue(0)
            self.lbl_status.setText("Aguardando...")
            QMessageBox.warning(
                self, "Aviso",
                "Nenhum dado válido foi extraído dos arquivos.\nVerifique se são arquivos SIA/SIH válidos."
            )
            return

        self.progress.setValue(100)
        self.lbl_status.setText("Concluído!")
        self.on_processed(df)

    def _on_failed(self, msg):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("INICIAR PROCESSAMENTO")
        self.progress.setValue(0)
        self.lbl_status.setText("Erro.")
        QMessageBox.critical(self, "Erro Crítico", f"Falha no processamento:\n{msg}")
