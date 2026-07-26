"""Tela 3: Tabela Dinâmica - builder de pivot (campos, filtros, templates, tema)."""
import json
import logging

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFontMetrics, QStandardItemModel, QStandardItem, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QListWidget, QListWidgetItem, QAbstractItemView, QFrame, QScrollArea,
    QTreeView, QTabWidget, QMenu, QMessageBox, QApplication, QInputDialog,
    QHeaderView,
)

from ui_qt import theme
from ui_qt.main_window import dados_path
from ui_qt.dialogs import FilterDialog, DialogoExportacao
from ui_qt.delegates import SelecaoForteDelegate

TEMPLATES_PATH = dados_path("templates.json")

# Cor de texto FIXA da árvore da Tabela Dinâmica — independe do tema geral do
# app, pois o fundo das células (PIVOT_PALETTES) é sempre claro; num tema
# escuro, theme.TEXT ficaria claro e o texto sumiria sobre esse fundo.
_TEXTO_PIVOT = "#1A1A1A"


class _PivotTreeView(QTreeView):
    """QTreeView que estende o fundo da linha até a borda esquerda —
    por padrão o Qt só pinta o fundo a partir do texto, deixando a área do
    recuo/seta de expandir com a cor base da view."""

    def drawRow(self, painter, options, index):
        cor = index.data(Qt.BackgroundRole)
        if cor is not None:
            painter.save()
            painter.fillRect(options.rect, cor)
            painter.restore()
        super().drawRow(painter, options, index)


def _fmt(v):
    try:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(v)


def _carregar_templates():
    defaults = {}
    try:
        with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
            defaults.update(json.load(f))
    except FileNotFoundError:
        pass
    except Exception:
        logging.exception("Falha ao carregar templates de %s", TEMPLATES_PATH)
    if not defaults:
        defaults = {"1. Resumo": {"rows": ["Hospital/Prestador"], "cols": [], "filters": {}}}
    return defaults


def _salvar_templates(templates):
    """Grava templates.json; retorna True em caso de sucesso."""
    try:
        with open(TEMPLATES_PATH, "w", encoding="utf-8") as f:
            json.dump(templates, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        logging.exception("Falha ao salvar templates em %s", TEMPLATES_PATH)
        return False


class PivotPage(QWidget):
    """Container com abas — cada aba é uma análise dinâmica independente."""

    def __init__(self):
        super().__init__()
        self.tabs = []
        self._contador = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        bar = QHBoxLayout()
        btn_nova = QPushButton("+ Nova Análise")
        btn_nova.clicked.connect(lambda: self.nova_aba(self._df_base))
        bar.addWidget(btn_nova)
        bar.addStretch(1)
        layout.addLayout(bar)

        self.tabwidget = QTabWidget()
        self.tabwidget.setTabsClosable(True)
        self.tabwidget.tabCloseRequested.connect(self._fechar_aba)
        layout.addWidget(self.tabwidget, 1)

        self._df_base = None

    def nova_aba(self, df):
        self._df_base = df
        self._contador += 1
        aba = PivotTab(df, self._contador)
        self.tabs.append(aba)
        idx = self.tabwidget.addTab(aba, f"Análise #{self._contador}")
        self.tabwidget.setCurrentIndex(idx)
        return aba

    def _fechar_aba(self, idx):
        widget = self.tabwidget.widget(idx)
        if widget in self.tabs:
            self.tabs.remove(widget)
        self.tabwidget.removeTab(idx)
        widget.deleteLater()


class PivotTab(QWidget):
    def __init__(self, df, index_id):
        super().__init__()
        self.id_dinamico = index_id

        self.df_orig = df.copy().fillna(0)
        if "Financiamento" in self.df_orig.columns:
            self.df_orig["Financiamento"] = self.df_orig["Financiamento"].astype(str).replace(
                ["MAC", "Média e Alta Complexidade", "Media e Alta Complexidade", "(MAC)"], "MAC"
            )
        if "Valor" in self.df_orig.columns:
            self.df_orig["Valor"] = pd.to_numeric(self.df_orig["Valor"], errors="coerce").fillna(0.0)
        for c in self.df_orig.columns:
            if c != "Valor":
                self.df_orig[c] = self.df_orig[c].astype(str)

        self.df_filtrado_cache = self.df_orig.copy()
        self.cols_disponiveis = [c for c in self.df_orig.columns if c != "Valor"]
        self.active_rows = []
        self.active_cols = []
        self.active_filters = {}
        self.quick_filter_hospital = None
        self.templates = _carregar_templates()
        self._sort_col = None
        self._sort_reverse = False

        root = QHBoxLayout(self)

        # ============ PAINEL ESQUERDO ============
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFixedWidth(260)
        left_inner = QWidget()
        self.left_layout = QVBoxLayout(left_inner)
        left_scroll.setWidget(left_inner)
        root.addWidget(left_scroll)

        self._secao_campos()
        self._secao_ativos()
        self.left_layout.addStretch(1)

        # ============ CENTRO ============
        center = QVBoxLayout()
        root.addLayout(center, 1)

        self.lbl_status = QLabel()
        self.lbl_status.setObjectName("StatusTotal")
        center.addWidget(self.lbl_status)

        self.tree = _PivotTreeView()
        self.tree.setItemDelegate(SelecaoForteDelegate(self.tree))
        self.tree.setAlternatingRowColors(False)
        self.tree.setUniformRowHeights(False)
        self.tree.setWordWrap(True)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._menu_contexto_tree)
        self.tree.header().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.header().customContextMenuRequested.connect(self._menu_cabecalho_tree)
        center.addWidget(self.tree, 1)

        QShortcut(QKeySequence.Copy, self.tree, self._copiar_selecao)
        QShortcut(QKeySequence.SelectAll, self.tree, self.tree.selectAll)

        # ============ PAINEL DIREITO ============
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFixedWidth(300)
        right_inner = QWidget()
        self.right_layout = QVBoxLayout(right_inner)
        right_scroll.setWidget(right_inner)
        root.addWidget(right_scroll)

        self._secao_quick_filters()

        self.right_layout.addSpacing(14)
        self.right_layout.addWidget(self._separador())
        self.right_layout.addSpacing(14)

        self._secao_templates()

        self.right_layout.addSpacing(14)
        self.right_layout.addWidget(self._separador())
        self.right_layout.addSpacing(14)

        self.right_layout.addWidget(self._titulo_secao("Aparência (tabela)"))
        self.right_layout.addSpacing(6)
        self.cb_tema = QComboBox()
        self.cb_tema.addItems(list(theme.PIVOT_PALETTES.keys()))
        tema_salvo = self.templates.get("_config_geral_", {}).get("ultimo_tema", "Azul")
        if tema_salvo in theme.PIVOT_PALETTES:
            self.cb_tema.setCurrentText(tema_salvo)
        self.cb_tema.currentTextChanged.connect(self._mudar_tema)
        self.right_layout.addWidget(self.cb_tema)
        self.right_layout.addStretch(1)

        btn_export = QPushButton("Exportar Excel")
        btn_export.clicked.connect(self._exportar)
        self.right_layout.addWidget(btn_export)

        if "Hospital/Prestador" in self.cols_disponiveis:
            self._add_to_active("Hospital/Prestador", "row")
        self._render_ativos()
        self._calcular_pivot()

    # ================= SEÇÕES DO PAINEL DIREITO =================
    def _secao_quick_filters(self):
        self.right_layout.addWidget(self._titulo_secao("Filtro Rápido (Hospital)"))
        self.right_layout.addSpacing(6)
        self.fr_quick = QVBoxLayout()
        self.fr_quick.setSpacing(6)
        self.right_layout.addLayout(self.fr_quick)
        self._render_quick_filters()

    def _render_quick_filters(self):
        while self.fr_quick.count():
            item = self.fr_quick.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if "Hospital/Prestador" not in self.df_orig.columns:
            return
        hospitais = sorted(self.df_orig["Hospital/Prestador"].unique())
        for hosp in hospitais:
            ativo = self.quick_filter_hospital == hosp
            btn = QPushButton(hosp[:33])
            btn.setCheckable(True)
            btn.setChecked(ativo)
            btn.setToolTip(hosp)
            btn.clicked.connect(lambda checked=False, h=hosp: self._toggle_quick_filter(h))
            self.fr_quick.addWidget(btn)

    def _toggle_quick_filter(self, hospital):
        if self.quick_filter_hospital == hospital:
            self.quick_filter_hospital = None
            self.active_filters.pop("Hospital/Prestador", None)
        else:
            self.quick_filter_hospital = hospital
            self.active_filters["Hospital/Prestador"] = {hospital}
        self._render_quick_filters()
        self._render_ativos()
        self._calcular_pivot()

    def _secao_templates(self):
        self.right_layout.addWidget(self._titulo_secao("Modelos Salvos"))
        self.right_layout.addSpacing(6)
        btn_novo = QPushButton("+ Novo Modelo")
        btn_novo.clicked.connect(self._gravar_template)
        self.right_layout.addWidget(btn_novo)
        self.right_layout.addSpacing(6)
        self.fr_templates = QVBoxLayout()
        self.fr_templates.setSpacing(6)
        self.right_layout.addLayout(self.fr_templates)
        self._render_templates()

    def _render_templates(self):
        while self.fr_templates.count():
            item = self.fr_templates.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for nome in self.templates:
            if nome == "_config_geral_":
                continue
            row = QHBoxLayout()
            btn = QPushButton(nome)
            btn.clicked.connect(lambda checked=False, n=nome: self._aplicar_template(n))
            row.addWidget(btn, 1)
            btn_del = QPushButton("×")
            btn_del.setObjectName("IconBtn")
            btn_del.setFixedWidth(28)
            btn_del.clicked.connect(lambda checked=False, n=nome: self._excluir_template(n))
            row.addWidget(btn_del)
            self.fr_templates.addLayout(row)

    def _gravar_template(self):
        nome, ok = QInputDialog.getText(self, "Salvar Modelo", "Nome do novo modelo:")
        if not ok or not nome.strip():
            return
        self.templates[nome.strip()] = {
            "rows": list(self.active_rows),
            "cols": list(self.active_cols),
            "filters": {c: list(v) for c, v in self.active_filters.items()},
        }
        if not _salvar_templates(self.templates):
            QMessageBox.warning(
                self, "Aviso",
                f"O modelo '{nome.strip()}' foi criado nesta sessão, mas não\n"
                f"foi possível gravá-lo em disco (veja erro_log.txt).",
            )
        self._render_templates()

    def _aplicar_template(self, nome):
        cfg = self.templates.get(nome)
        if not cfg:
            return
        self.active_rows = [c for c in cfg.get("rows", []) if c in self.cols_disponiveis]
        self.active_cols = [c for c in cfg.get("cols", []) if c in self.cols_disponiveis]
        self.active_filters = {}
        for col, vals in cfg.get("filters", {}).items():
            if col in self.df_orig.columns:
                self.active_filters[col] = set(vals)
        self.quick_filter_hospital = self.active_filters.get("Hospital/Prestador")
        if isinstance(self.quick_filter_hospital, set) and len(self.quick_filter_hospital) == 1:
            self.quick_filter_hospital = next(iter(self.quick_filter_hospital))
        else:
            self.quick_filter_hospital = None
        self._render_quick_filters()
        self._render_ativos()
        self._calcular_pivot()

    def _excluir_template(self, nome):
        self.templates.pop(nome, None)
        _salvar_templates(self.templates)
        self._render_templates()

    def _titulo_secao(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("SectionTitle")
        return lbl

    def _separador(self):
        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setObjectName("Separador")
        return linha

    def _secao_campos(self):
        self.left_layout.addWidget(self._titulo_secao("Campos Disponíveis"))
        self.left_layout.addSpacing(6)
        self.fr_campos = QVBoxLayout()
        self.fr_campos.setSpacing(6)
        self.left_layout.addLayout(self.fr_campos)
        for col in self.cols_disponiveis:
            row = QHBoxLayout()
            row.addWidget(QLabel(col[:26]), 1)
            btn_row = QPushButton("≡")
            btn_row.setObjectName("IconBtn")
            btn_row.setFixedWidth(28)
            btn_row.setToolTip("Adicionar em Linhas")
            btn_row.clicked.connect(lambda checked=False, c=col: self._add_to_active(c, "row"))
            row.addWidget(btn_row)
            btn_col = QPushButton("||")
            btn_col.setObjectName("IconBtn")
            btn_col.setFixedWidth(28)
            btn_col.setToolTip("Adicionar em Colunas")
            btn_col.clicked.connect(lambda checked=False, c=col: self._add_to_active(c, "col"))
            row.addWidget(btn_col)
            btn_y = QPushButton("Y")
            btn_y.setObjectName("IconBtn")
            btn_y.setFixedWidth(28)
            btn_y.setToolTip("Adicionar como filtro")
            btn_y.clicked.connect(lambda checked=False, c=col: self._add_filter(c))
            row.addWidget(btn_y)
            self.fr_campos.addLayout(row)

    def _secao_ativos(self):
        self.left_layout.addSpacing(14)
        self.left_layout.addWidget(self._separador())
        self.left_layout.addSpacing(14)

        self.left_layout.addWidget(self._titulo_secao("Linhas"))
        self.left_layout.addSpacing(6)
        self.lst_rows = QListWidget()
        self.lst_rows.setDragDropMode(QAbstractItemView.InternalMove)
        self.lst_rows.setFixedHeight(90)
        self.lst_rows.itemDoubleClicked.connect(lambda it: self._remove_active(it.text(), "row"))
        self.lst_rows.model().rowsMoved.connect(lambda *a: self._sync_ordem("row"))
        self.left_layout.addWidget(self.lst_rows)

        self.left_layout.addSpacing(14)
        self.left_layout.addWidget(self._separador())
        self.left_layout.addSpacing(14)

        self.left_layout.addWidget(self._titulo_secao("Colunas"))
        self.left_layout.addSpacing(6)
        self.lst_cols = QListWidget()
        self.lst_cols.setDragDropMode(QAbstractItemView.InternalMove)
        self.lst_cols.setFixedHeight(90)
        self.lst_cols.itemDoubleClicked.connect(lambda it: self._remove_active(it.text(), "col"))
        self.lst_cols.model().rowsMoved.connect(lambda *a: self._sync_ordem("col"))
        self.left_layout.addWidget(self.lst_cols)

        self.left_layout.addSpacing(14)
        self.left_layout.addWidget(self._separador())
        self.left_layout.addSpacing(14)

        self.left_layout.addWidget(self._titulo_secao("Filtros Ativos"))
        self.left_layout.addSpacing(6)
        self.fr_filtros = QVBoxLayout()
        self.left_layout.addLayout(self.fr_filtros)

    def _render_ativos(self):
        self.lst_rows.blockSignals(True)
        self.lst_rows.clear()
        for c in self.active_rows:
            self.lst_rows.addItem(QListWidgetItem(c))
        self.lst_rows.blockSignals(False)

        self.lst_cols.blockSignals(True)
        self.lst_cols.clear()
        for c in self.active_cols:
            self.lst_cols.addItem(QListWidgetItem(c))
        self.lst_cols.blockSignals(False)

        while self.fr_filtros.count():
            item = self.fr_filtros.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.active_filters:
            lbl = QLabel("Clique em 'Y' na lista de campos.")
            lbl.setObjectName("Muted")
            lbl.setStyleSheet("font-size: 9pt;")
            self.fr_filtros.addWidget(lbl)
        for col, vals in self.active_filters.items():
            self.fr_filtros.addWidget(self._criar_card_filtro(col, vals))

    def _criar_card_filtro(self, col, vals):
        card = QFrame()
        card.setObjectName("Card")
        lay = QVBoxLayout(card)
        head = QHBoxLayout()
        head.addWidget(QLabel(f"<b>{col}</b>"), 1)
        btn_edit = QPushButton("⚙")
        btn_edit.setObjectName("IconBtn")
        btn_edit.setFixedWidth(28)
        btn_edit.clicked.connect(lambda checked=False, c=col: self._editar_filtro(c))
        head.addWidget(btn_edit)
        btn_del = QPushButton("×")
        btn_del.setObjectName("IconBtn")
        btn_del.setFixedWidth(28)
        btn_del.clicked.connect(lambda checked=False, c=col: self._remove_filter(c))
        head.addWidget(btn_del)
        lay.addLayout(head)

        total = self.df_orig[col].nunique()
        sel = len(vals)
        if sel == total:
            resumo = "(Todos)"
        elif sel <= 3:
            resumo = ", ".join(list(vals)[:3])
        else:
            resumo = f"{', '.join(list(vals)[:2])} (+{sel - 2})"
        lbl = QLabel(resumo)
        lbl.setObjectName("Muted")
        lbl.setStyleSheet("font-size: 9pt;")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        return card

    def _sync_ordem(self, tipo):
        lst = self.lst_rows if tipo == "row" else self.lst_cols
        nova_ordem = [lst.item(i).text() for i in range(lst.count())]
        if tipo == "row":
            self.active_rows = nova_ordem
        else:
            self.active_cols = nova_ordem
        self._calcular_pivot()

    # ================= AÇÕES DE CAMPOS =================
    def _add_to_active(self, col, tipo):
        if tipo == "row":
            if col not in self.active_rows:
                self.active_rows.append(col)
            if col in self.active_cols:
                self.active_cols.remove(col)
        else:
            if col not in self.active_cols:
                self.active_cols.append(col)
            if col in self.active_rows:
                self.active_rows.remove(col)
        self._render_ativos()
        self._calcular_pivot()

    def _remove_active(self, col, tipo):
        try:
            if tipo == "row":
                self.active_rows.remove(col)
            else:
                self.active_cols.remove(col)
        except ValueError:
            pass
        self._render_ativos()
        self._calcular_pivot()

    def _add_filter(self, col):
        if col not in self.active_filters:
            self.active_filters[col] = set(self.df_orig[col].unique())
        self._render_ativos()
        self._editar_filtro(col)

    def _editar_filtro(self, col):
        valores = self.df_orig[col].tolist()
        atuais = self.active_filters.get(col, set(self.df_orig[col].unique()))
        dlg = FilterDialog(self, col, valores, atuais, lambda sel: self._aplicar_filtro(col, sel))
        dlg.exec()

    def _aplicar_filtro(self, col, selecionados):
        self.active_filters[col] = set(selecionados)
        if col == "Hospital/Prestador":
            self.quick_filter_hospital = selecionados[0] if len(selecionados) == 1 else None
            self._render_quick_filters()
        self._render_ativos()
        self._calcular_pivot()

    def _remove_filter(self, col):
        self.active_filters.pop(col, None)
        if col == "Hospital/Prestador":
            self.quick_filter_hospital = None
            self._render_quick_filters()
        self._render_ativos()
        self._calcular_pivot()

    def _mudar_tema(self, novo_tema):
        self.templates.setdefault("_config_geral_", {})["ultimo_tema"] = novo_tema
        _salvar_templates(self.templates)
        self._calcular_pivot()

    # ================= CÁLCULO E RENDERIZAÇÃO DO PIVOT =================
    def _calcular_pivot(self):
        try:
            df = self.df_orig.copy()
            for col, allowed in self.active_filters.items():
                if col in df.columns:
                    df = df[df[col].isin(allowed)]
            self.df_filtrado_cache = df

            if not self.active_rows:
                self.tree.setModel(QStandardItemModel())
                total = df["Valor"].sum()
                self.lbl_status.setText(f"Total Geral: {_fmt(total)}")
                return

            if set(self.active_rows) & set(self.active_cols):
                self.lbl_status.setText("Erro: coluna repetida em Linhas e Colunas.")
                return

            if not self.active_cols:
                piv = df.groupby(self.active_rows)["Valor"].sum().reset_index()
                d_cols = ["Valor"]
            else:
                piv = pd.pivot_table(df, values="Valor", index=self.active_rows,
                                      columns=self.active_cols, aggfunc="sum", fill_value=0)
                piv["Total"] = piv.sum(axis=1)
                piv = piv.reset_index()
                new_cols = []
                for c in piv.columns:
                    if isinstance(c, tuple):
                        new_cols.append(" - ".join(str(x) for x in c if x))
                    else:
                        new_cols.append(str(c))
                piv.columns = new_cols
                d_cols = [c for c in piv.columns if c not in self.active_rows]

            model = QStandardItemModel()
            model.setHorizontalHeaderLabels([" / ".join(self.active_rows)] + d_cols)

            fm = QFontMetrics(self.tree.font())
            # Largura mínima de cada coluna de valor = a maior string formatada
            # que ela vai exibir (cabeçalho incluído). Começa a partir do
            # cabeçalho e cresce conforme os valores são formatados abaixo.
            larguras_valores = [fm.horizontalAdvance(c) + 28 for c in d_cols]
            # Larguras dos rótulos (nomes) que vão aparecer na coluna 0, em
            # qualquer nível da hierarquia — usadas para a coluna de nomes
            # nunca ficar pequena demais pra identificar a linha (ver abaixo).
            larguras_rotulos = []

            passos_cor = theme.PIVOT_PALETTES.get(self.cb_tema.currentText(), theme.PIVOT_PALETTES["Azul"])

            def cor_por_profundidade(depth):
                # Grupo mais geral (nível 0) = cor mais forte; níveis mais
                # específicos vão clareando (estilo planilha tradicional).
                n = len(passos_cor)
                idx = max(0, n - 1 - min(depth, n - 1))
                return QColor(passos_cor[idx])

            def montar(sub, niveis, depth):
                lvl = niveis[0]
                grupos = []
                for nome, g in sub.groupby(lvl):
                    soma = g[d_cols].sum()
                    if self._sort_col == "__label__":
                        chave = str(nome)
                    elif self._sort_col in d_cols:
                        chave = soma[self._sort_col]
                    else:
                        chave = soma.sum()
                    grupos.append((chave, nome, g, soma))
                grupos.sort(key=lambda x: x[0], reverse=self._sort_reverse if self._sort_col else True)

                linhas = []
                bg = cor_por_profundidade(depth)
                for _, nome, g, soma in grupos:
                    item_label = QStandardItem(str(nome))
                    item_label.setEditable(False)
                    item_label.setBackground(bg)
                    item_label.setForeground(QColor(_TEXTO_PIVOT))
                    larguras_rotulos.append(fm.horizontalAdvance(str(nome)) + 24 + depth * 20)
                    valores_item = [item_label]
                    for idx_col, c in enumerate(d_cols):
                        texto_valor = _fmt(soma[c])
                        it = QStandardItem(texto_valor)
                        it.setEditable(False)
                        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        it.setBackground(bg)
                        it.setForeground(QColor(_TEXTO_PIVOT))
                        valores_item.append(it)
                        largura_texto = fm.horizontalAdvance(texto_valor) + 28
                        if largura_texto > larguras_valores[idx_col]:
                            larguras_valores[idx_col] = largura_texto
                    if len(niveis) > 1:
                        filhos = montar(g, niveis[1:], depth + 1)
                        for linha_filha in filhos:
                            item_label.appendRow(linha_filha)
                    linhas.append(valores_item)
                return linhas

            for linha in montar(piv, self.active_rows, 0):
                model.appendRow(linha)

            self.tree.setModel(model)
            self.tree.expandAll()

            # Colunas de valor: largura fixa, exatamente a mínima necessária.
            # Coluna de rótulo: ocupa todo o espaço que sobrar (Stretch); só
            # quando as colunas de valor já não cabem é que entra rolagem
            # horizontal (comportamento automático do QHeaderView/scroll area).
            # A coluna de rótulo nunca fica menor que 40% do maior rótulo da
            # árvore — abaixo disso a linha de quebra de texto entra em ação
            # em vez de espremer ainda mais.
            maior_rotulo = max(larguras_rotulos) if larguras_rotulos else 200
            largura_minima_rotulo = max(160, int(maior_rotulo * 0.4))

            header = self.tree.header()
            header.setMinimumSectionSize(largura_minima_rotulo)
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            for i, largura in enumerate(larguras_valores, start=1):
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                self.tree.setColumnWidth(i, largura)

            self.lbl_status.setText(f"Total Processado: {_fmt(df['Valor'].sum())}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    # ================= ORDENAÇÃO / MENUS =================
    def _menu_cabecalho_tree(self, pos):
        col_idx = self.tree.header().logicalIndexAt(pos)
        model = self.tree.model()
        if model is None:
            return
        nome_col = model.headerData(col_idx, Qt.Horizontal)
        menu = QMenu(self)
        menu.addAction("Classificar A-Z", lambda: self._ordenar(nome_col, False))
        menu.addAction("Classificar Z-A", lambda: self._ordenar(nome_col, True))
        menu.exec(self.tree.header().mapToGlobal(pos))

    def _ordenar(self, nome_col, reverse):
        label_header = " / ".join(self.active_rows)
        self._sort_col = "__label__" if nome_col == label_header else nome_col
        self._sort_reverse = reverse
        self._calcular_pivot()

    def _menu_contexto_tree(self, pos):
        menu = QMenu(self)
        menu.addAction("Copiar Seleção", self._copiar_selecao)
        menu.addAction("Selecionar Tudo", self.tree.selectAll)
        menu.addSeparator()
        menu.addAction("Expandir Tudo", self.tree.expandAll)
        menu.addAction("Recolher Tudo", self.tree.collapseAll)
        menu.addSeparator()
        menu.addAction("Exportar Excel", self._exportar)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _copiar_selecao(self):
        sel_model = self.tree.selectionModel()
        if not sel_model:
            return
        idxs = sel_model.selectedIndexes()
        if not idxs:
            return
        model = self.tree.model()
        # Agrupa por posição visual (linha na árvore) em vez de (row, parent) —
        # assim funciona mesmo quando a seleção cobre células de níveis
        # diferentes da hierarquia (seleção livre, tipo Excel).
        por_linha = {}
        for idx in idxs:
            y = self.tree.visualRect(idx).y()
            por_linha.setdefault(y, {})[idx.column()] = model.data(idx) or ""
        linhas = [
            "\t".join(str(cols[c]) for c in sorted(cols))
            for _, cols in sorted(por_linha.items())
        ]
        QApplication.clipboard().setText("\n".join(linhas))

    def _exportar(self):
        # A base completa não está disponível aqui isoladamente; a exportação
        # combinada (base + pivots) é feita a partir da tela de Dados Brutos.
        dlg = DialogoExportacao(self, self.df_orig, [self])
        dlg.exec()
