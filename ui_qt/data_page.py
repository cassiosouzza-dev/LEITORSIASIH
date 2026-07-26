"""Tela 2: Dados Brutos - tabela completa extraída, com ordenação, filtro e cópia."""
import logging
import os

import pandas as pd
from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, QLabel,
    QAbstractItemView, QMenu, QMessageBox, QApplication,
)

from ui_qt.dialogs import FilterDialog, DialogoExportacao
from ui_qt.delegates import SelecaoForteDelegate
from ui_qt.main_window import dados_path

SERIE_HISTORICA_PATH = dados_path("Serie_historica.xlsx")


def _formatar_valor(v):
    try:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(v)


class PandasModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        col = self._df.columns[index.column()]
        val = self._df.iat[index.row(), index.column()]
        if role == Qt.DisplayRole:
            if col == "Valor" and isinstance(val, (int, float)):
                return _formatar_valor(val)
            return "" if pd.isna(val) else str(val)
        if role == Qt.TextAlignmentRole and col == "Valor":
            return Qt.AlignRight | Qt.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)

    def set_dataframe(self, df):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def dataframe(self):
        return self._df

    def column_name(self, col_idx):
        return self._df.columns[col_idx]


class DataPage(QWidget):
    def __init__(self, df, on_open_pivot):
        super().__init__()
        self.df_orig = df.reset_index(drop=True)
        self.active_filters = {}
        self.on_open_pivot = on_open_pivot
        self.pivot_tabs_abertas = []
        self.pivot_page = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)

        bar = QHBoxLayout()
        self.btn_hist = QPushButton("Adicionar ao Histórico")
        self.btn_hist.clicked.connect(self._adicionar_historico)
        bar.addWidget(self.btn_hist)

        self.btn_pivot = QPushButton("Tabela Dinâmica")
        self.btn_pivot.setObjectName("Primary")
        self.btn_pivot.clicked.connect(self._abrir_pivot)
        bar.addWidget(self.btn_pivot)

        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.clicked.connect(self._exportar)
        bar.addWidget(self.btn_export)

        bar.addStretch(1)
        self.lbl_contagem = QLabel()
        bar.addWidget(self.lbl_contagem)
        layout.addLayout(bar)

        self.model = PandasModel(self.df_orig)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setItemDelegate(SelecaoForteDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._menu_celula)

        header = self.table.horizontalHeader()
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._menu_cabecalho)

        layout.addWidget(self.table, 1)

        QShortcut(QKeySequence.Copy, self.table, self._copiar_selecao)

        self._atualizar_contagem()
        self.table.resizeColumnsToContents()

    # ---------------- CÓPIA ----------------
    def _copiar_selecao(self):
        idxs = self.table.selectionModel().selectedIndexes()
        if not idxs:
            return
        idxs.sort(key=lambda i: (i.row(), i.column()))
        linhas = {}
        for i in idxs:
            linhas.setdefault(i.row(), {})[i.column()] = self.model.data(i, Qt.DisplayRole) or ""
        texto = "\n".join(
            "\t".join(str(cols[c]) for c in sorted(cols))
            for _, cols in sorted(linhas.items())
        )
        QApplication.clipboard().setText(texto)

    # ---------------- MENUS ----------------
    def _menu_celula(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        col_name = self.model.column_name(index.column())
        valor = self.model.data(index, Qt.DisplayRole)

        menu = QMenu(self)
        menu.addAction(f"Copiar: '{str(valor)[:20]}'", self._copiar_selecao)
        menu.addAction("Copiar Linha(s) Selecionada(s)", self._copiar_selecao)
        menu.addSeparator()
        menu.addAction(f"Filtrar por: {str(valor)[:20]}", lambda: self._aplicar_filtro(col_name, [str(valor)]))
        menu.addAction("Remover Filtros desta Coluna", lambda: self._remover_filtro(col_name))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _menu_cabecalho(self, pos):
        col_idx = self.table.horizontalHeader().logicalIndexAt(pos)
        if col_idx < 0:
            return
        col_name = self.model.column_name(col_idx)

        menu = QMenu(self)
        menu.addAction("Classificar A-Z", lambda: self._ordenar(col_name, False))
        menu.addAction("Classificar Z-A", lambda: self._ordenar(col_name, True))
        menu.addSeparator()
        menu.addAction("Filtrar...", lambda: self._abrir_filtro(col_name))
        menu.exec(self.table.horizontalHeader().mapToGlobal(pos))

    # ---------------- ORDENAÇÃO / FILTRO ----------------
    def _ordenar(self, col, reverse):
        df = self.model.dataframe().sort_values(by=col, ascending=not reverse, kind="mergesort")
        self.model.set_dataframe(df.reset_index(drop=True))

    def _abrir_filtro(self, col):
        valores = self.df_orig[col].astype(str).tolist()
        atuais = self.active_filters.get(col, set(self.df_orig[col].astype(str).unique()))
        dlg = FilterDialog(self, col, valores, atuais, lambda sel: self._aplicar_filtro(col, sel))
        dlg.exec()

    def _aplicar_filtro(self, col, selecionados):
        total_unicos = self.df_orig[col].astype(str).nunique()
        if len(selecionados) >= total_unicos:
            self.active_filters.pop(col, None)
        else:
            self.active_filters[col] = set(selecionados)
        self._recalcular_view()

    def _remover_filtro(self, col):
        self.active_filters.pop(col, None)
        self._recalcular_view()

    def _recalcular_view(self):
        df = self.df_orig
        for col, vals in self.active_filters.items():
            df = df[df[col].astype(str).isin(vals)]
        self.model.set_dataframe(df.reset_index(drop=True))
        self._atualizar_contagem()

    def _atualizar_contagem(self):
        total = len(self.df_orig)
        atual = len(self.model.dataframe())
        if atual == total:
            self.lbl_contagem.setText(f"{total} registros")
        else:
            self.lbl_contagem.setText(f"{atual} de {total} registros (filtrado)")

    # ---------------- AÇÕES ----------------
    def _abrir_pivot(self):
        self.on_open_pivot(self.df_orig, self)

    def _exportar(self):
        dlg = DialogoExportacao(self, self.df_orig, self.pivot_tabs_abertas)
        dlg.exec()

    def _adicionar_historico(self):
        try:
            novos_dados_resumo = self.df_orig[
                ["Hospital/Prestador", "Mês/Ano", "Âmbito Serviço"]
            ].drop_duplicates().values.tolist()
        except Exception:
            logging.exception("Falha ao calcular resumo para checagem de duplicados no histórico")
            novos_dados_resumo = []

        msg = f"Deseja adicionar {len(self.df_orig)} registros ao arquivo '{SERIE_HISTORICA_PATH}'?"
        substituir = False

        if os.path.exists(SERIE_HISTORICA_PATH):
            try:
                df_hist = pd.read_excel(SERIE_HISTORICA_PATH)
                colunas_chave = ["Hospital/Prestador", "Mês/Ano", "Âmbito Serviço"]
                if novos_dados_resumo and all(c in df_hist.columns for c in colunas_chave):
                    conflitos = []
                    for hospital, mes, ambito in novos_dados_resumo:
                        filtro = (
                            (df_hist["Hospital/Prestador"] == hospital)
                            & (df_hist["Mês/Ano"] == mes)
                            & (df_hist["Âmbito Serviço"] == ambito)
                        )
                        if not df_hist[filtro].empty:
                            conflitos.append(f"- {hospital} — {ambito} de {mes}")
                    if conflitos:
                        lista_str = "\n".join(conflitos)
                        msg = (
                            f"Atenção: já existem dados salvos para:\n{lista_str}\n\n"
                            "Se confirmar, os dados ANTIGOS desses períodos serão SUBSTITUÍDOS pelos novos.\n\n"
                            "Deseja substituir os dados antigos pelos novos?"
                        )
                        substituir = True
            except Exception:
                logging.exception("Erro ao ler histórico para verificação em %s", SERIE_HISTORICA_PATH)

        resposta = QMessageBox.question(self, "Confirmar Histórico", msg)
        if resposta != QMessageBox.Yes:
            return

        try:
            df_final = self.df_orig.copy()
            novo_arquivo = not os.path.exists(SERIE_HISTORICA_PATH)

            if not novo_arquivo:
                df_hist = pd.read_excel(SERIE_HISTORICA_PATH)
                if substituir and novos_dados_resumo:
                    for hospital, mes, ambito in novos_dados_resumo:
                        mascara = ~(
                            (df_hist["Hospital/Prestador"] == hospital)
                            & (df_hist["Mês/Ano"] == mes)
                            & (df_hist["Âmbito Serviço"] == ambito)
                        )
                        df_hist = df_hist[mascara]
                df_final = pd.concat([df_hist, df_final], ignore_index=True)

            df_final.to_excel(SERIE_HISTORICA_PATH, index=False)
            try:
                from prod_SIA_SIH2xlsx import formatar_excel_como_tabela
                formatar_excel_como_tabela(SERIE_HISTORICA_PATH)
            except Exception:
                logging.exception("Falha ao formatar %s como tabela", SERIE_HISTORICA_PATH)

            acao = "criado" if novo_arquivo else ("atualizado (substituição)" if substituir else "atualizado (adição)")
            QMessageBox.information(
                self, "Sucesso", f"Histórico {acao} com sucesso!\n\nTotal de registros na série: {len(df_final)}"
            )
        except PermissionError:
            QMessageBox.critical(
                self, "Erro", f"O arquivo '{SERIE_HISTORICA_PATH}' está aberto no Excel.\nFeche-o e tente novamente."
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro Crítico", f"Falha ao salvar:\n{e}")
