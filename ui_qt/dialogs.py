"""Diálogos reutilizáveis: filtro por valores e exportação para Excel."""
import os

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QCheckBox, QLabel, QFileDialog, QMessageBox, QScrollArea, QWidget,
)

from prod_SIA_SIH2xlsx import formatar_excel_como_tabela


class FilterDialog(QDialog):
    """Lista com busca e checkboxes para filtrar os valores de uma coluna."""

    def __init__(self, parent, titulo, valores, selecionados_atuais, on_apply):
        super().__init__(parent)
        self.setWindowTitle(f"Filtrar: {titulo}")
        self.resize(300, 450)
        self.on_apply = on_apply
        self.valores_unicos = sorted(set(str(v) for v in valores))
        self.selecionados_atuais = set(selecionados_atuais) if selecionados_atuais else set(self.valores_unicos)

        layout = QVBoxLayout(self)

        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Buscar...")
        self.busca.textChanged.connect(self._filtrar_lista)
        layout.addWidget(self.busca)

        self.chk_todos = QCheckBox("(Selecionar Todos)")
        self.chk_todos.setChecked(len(self.selecionados_atuais) == len(self.valores_unicos))
        self.chk_todos.stateChanged.connect(self._toggle_todos)
        layout.addWidget(self.chk_todos)

        self.lista = QListWidget()
        layout.addWidget(self.lista, 1)
        self._preencher_lista(self.valores_unicos)

        btn_aplicar = QPushButton("Aplicar Filtro")
        btn_aplicar.setObjectName("Primary")
        btn_aplicar.clicked.connect(self._aplicar)
        layout.addWidget(btn_aplicar)

    def _preencher_lista(self, valores):
        self.lista.clear()
        for v in valores:
            item = QListWidgetItem(v)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if v in self.selecionados_atuais else Qt.Unchecked)
            self.lista.addItem(item)

    def _filtrar_lista(self, texto):
        texto = texto.lower()
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            item.setHidden(texto not in item.text().lower())

    def _toggle_todos(self, state):
        novo = Qt.Checked if state == Qt.Checked.value else Qt.Unchecked
        for i in range(self.lista.count()):
            self.lista.item(i).setCheckState(novo)

    def _aplicar(self):
        selecionados = [
            self.lista.item(i).text()
            for i in range(self.lista.count())
            if self.lista.item(i).checkState() == Qt.Checked
        ]
        self.on_apply(selecionados)
        self.accept()


def exportar_dataframe_excel(parent, df, sheet_name="Base"):
    """Exportação simples (uma aba) usada pela tela de Dados Brutos."""
    caminho, _ = QFileDialog.getSaveFileName(parent, "Exportar Excel", "", "Excel (*.xlsx)")
    if not caminho:
        return
    if not caminho.lower().endswith(".xlsx"):
        caminho += ".xlsx"
    try:
        df.to_excel(caminho, sheet_name=sheet_name, index=False)
        formatar_excel_como_tabela(caminho)
        QMessageBox.information(parent, "OK", "Arquivo .xlsx salvo!")
        os.startfile(caminho)
    except Exception as e:
        QMessageBox.critical(parent, "Erro", f"Erro ao salvar (feche o arquivo se estiver aberto):\n{e}")


class DialogoExportacao(QDialog):
    """Exportação completa: base + cada Tabela Dinâmica aberta, em abas separadas."""

    def __init__(self, parent, df_completo, pivot_tabs):
        super().__init__(parent)
        self.setWindowTitle("Exportar")
        self.resize(380, 420)
        self.df = df_completo
        self.pivot_tabs = pivot_tabs  # lista de objetos com .id_dinamico, .active_rows, .active_cols, .df_filtrado_cache, .df_orig

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecione as abas:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        scroll.setWidget(inner)
        layout.addWidget(scroll, 1)

        self.chk_full = QCheckBox("Base Completa (Bruta)")
        self.chk_full.setChecked(True)
        inner_layout.addWidget(self.chk_full)

        self.chks_pivot = []
        for tab in self.pivot_tabs:
            chk = QCheckBox(f"Pivot #{tab.id_dinamico}")
            chk.setChecked(True)
            inner_layout.addWidget(chk)
            self.chks_pivot.append((chk, tab))
        inner_layout.addStretch(1)

        btn_salvar = QPushButton("Salvar Excel")
        btn_salvar.setObjectName("Primary")
        btn_salvar.clicked.connect(self._salvar)
        layout.addWidget(btn_salvar)

    def _salvar(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar Excel", "", "Excel (*.xlsx)")
        if not caminho:
            return
        if not caminho.lower().endswith(".xlsx"):
            caminho += ".xlsx"
        try:
            with pd.ExcelWriter(caminho, engine="openpyxl") as w:
                if self.chk_full.isChecked():
                    self.df.to_excel(w, sheet_name="Base", index=False)
                for chk, tab in self.chks_pivot:
                    if not chk.isChecked():
                        continue
                    rows = [r for r in tab.active_rows if r in tab.df_orig.columns]
                    cols = [c for c in tab.active_cols if c in tab.df_orig.columns]
                    df_f = tab.df_filtrado_cache
                    if rows:
                        if cols:
                            p = pd.pivot_table(df_f, values="Valor", index=rows, columns=cols, aggfunc="sum")
                        else:
                            p = df_f.groupby(rows)["Valor"].sum()
                        p.to_excel(w, sheet_name=f"Pivot_{tab.id_dinamico}", merge_cells=True)
                    else:
                        tab.df_orig.to_excel(w, sheet_name=f"Pivot_{tab.id_dinamico}", index=False)
            formatar_excel_como_tabela(caminho)
            QMessageBox.information(self, "OK", "Arquivo .xlsx salvo!")
            self.accept()
            os.startfile(caminho)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar (feche o arquivo se estiver aberto):\n{e}")
