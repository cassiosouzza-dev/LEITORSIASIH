# ==============================================================================
# SISTEMA DE EXTRAÇÃO DE DADOS SIA/SIH - VISUAL E JANELAS AUXILIARES
# ==============================================================================
# Autor: Cassio de Souza Lopes
# Data: 2024-06-10
# Versão: 1.0
# Descrição: Interface gráfica e janelas auxiliares para o sistema de extração
# ==============================================================================
# --- IMPORTAÇÕES ---
# ==============================================================================
# Bibliotecas padrão
# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
# Importa o TkinterDnD2 para drag-and-drop
from tkinterdnd2 import DND_FILES, TkinterDnD
# Bibliotecas adicionais
import pandas as pd
# Bibliotecas do sistema
import os
# Bibliotecas para logging e exceções
import sys
import threading
import traceback
import logging
# Bibliotecas para manipulação de arquivos e dados
import json
import re
# Bibliotecas para manipulação de fontes e ícones
from tkinter.font import Font

# Tenta importar a lógica de extração
try:
    # 1. Tenta importar da MESMA PASTA (o mais provável no seu caso)
    from prod_SIA_SIH2xlsx import executar_extracao_completa, formatar_excel_como_tabela

    print("SUCESSO: Extrator carregado da mesma pasta.")
except ImportError:
    try:
        # 2. Se falhar, tenta importar da pasta 'modulos'
        from modulos.prod_SIA_SIH2xlsx import executar_extracao_completa, formatar_excel_como_tabela

        print("SUCESSO: Extrator carregado da pasta 'modulos'.")
    except ImportError as e:
        # 3. Se falhar tudo, MOSTRA O ERRO REAL NO CONSOLE
        print(f"\nERRO CRÍTICO DE IMPORTAÇÃO: {e}")
        print("Verifique se o arquivo 'prod_SIA_SIH2xlsx.py' está na mesma pasta ou na pasta 'modulos'.\n")


        # Cria a função falsa só para o app abrir e você ver o erro
        def executar_extracao_completa(files, callback):
            import time
            # Aqui jogamos o erro na cara do usuário via interface
            callback(f"ERRO TÉCNICO: {str(e)}", 0)
            time.sleep(2)
            return pd.DataFrame()

        def formatar_excel_como_tabela(filename):
            pass

# --- CONFIGURAÇÃO DE LOG ---
logging.basicConfig(filename='erro_log.txt', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- FUNÇÃO GLOBAL DE LOG DE EXCEÇÕES ---
def log_exception(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    try:
        print("ERRO:", "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    except:
        pass

# --- APLICAÇÃO DA FUNÇÃO DE LOG GLOBAL ---
sys.excepthook = log_exception

# --- VISUAL ---
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("dark-blue")

# --- ÍCONES (Base64) ---
ICON_FILTER_B64 = "R0lGODlhEAAQCAYAAAC7vK7SAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAYdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuNWWFMmUAAABoSURBVDhPjYzbCoAgDIa9/4uuk66T8OIy20dDINJqDnSwHz7O1p8oIpH2xS3gOIq0bB845yANUNcbWCi3BEKjQSG1Bq04yH1kIAe5j0+Qh9xH3iAPuY+8QR5yH3mD/iH30X/iF1G9AIcKTiU1vtF/AAAAAElFTkSuQmCC"
ICON_UP_B64 = "R0lGODlhEAAQCAYAAAC7vK7SAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAtSURBVDhPYzhw4MB/SvD///8M2BSMmjBqwij4/580QJqmWeQYQKgfRk0YNWGQmgAAti+f+b+121gAAAAASUVORK5CYII="
ICON_DOWN_B64 = "R0lGODlhEAAQCAYAAAC7vK7SAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAtSURBVDhPYzhw4MB/SvD///8M2BSMmjBqwij4/580QJqmWeQYQKgfRk0YNWGQmgAAti+f+b+121gAAAAASUVORK5CYII="

# --- VERIFICAÇÃO DO PILLOW --- 
try: 
    from PIL import Image, ImageTk # NÃO REMOVER!
    TEM_PILLOW = True # Indica que o Pillow está disponível
except ImportError: 
    TEM_PILLOW = False # Indica que o Pillow NÃO está disponível

# função ressouce path recentes.json:
def resource_path(relative_path):
    """Retorna o caminho absoluto, funcionando tanto em Dev quanto no EXE"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

# --- FUNÇÃO DE ÍCONE CORRIGIDA (SEM .ICO, USA PNG DIRETO) ---
def aplicar_icone_global(janela):
    try:
        if not TEM_PILLOW:
            print("Pillow não instalado. Ícone não será carregado.")
            return

        # Pega a pasta onde está este script (siasihui.py)
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Lista de locais prováveis para o ícone
        locais = [
            os.path.join(base_path, "extrator_icon.png"),           # Pasta atual (modulos)
            os.path.join(os.path.dirname(base_path), "extrator_icon.png") # Pasta pai (raiz)
        ]
        
        icon_path = None
        for path in locais:
            if os.path.exists(path):
                icon_path = path
                break
            
        if icon_path:
            image = Image.open(icon_path)
            photo = ImageTk.PhotoImage(image)
            
            # Aplica na janela atual
            janela.wm_iconphoto(False, photo)
            janela.icon_photo_ref = photo # Salva referência pra não sumir
            
            # Tenta aplicar na raiz (se for Toplevel) para garantir
            try:
                janela.master.wm_iconphoto(False, photo)
            except:
                pass
        else:
            print(f"AVISO: 'extrator_icon.png' não encontrado em: {locais}")
            
    except Exception as e:
        print(f"Erro ao aplicar ícone: {e}")

# Classe base para janelas com ícone
class IconedToplevel(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Esconde a janela imediatamente ao criar
        self.withdraw()
        
        # 2. Aplica o ícone enquanto ela está oculta
        aplicar_icone_global(self)
        
        # 3. Força o sistema a computar as tarefas pendentes (pintura do fundo, etc)
        self.update_idletasks()
        
        # 4. Agenda para mostrar a janela daqui a 10ms.
        # Esse pequeno delay dá tempo ao Windows para processar a troca do ícone
        # e a aplicação do tema escuro ANTES de a janela ficar visível.
        self.after(10, self.deiconify)

        # Aplica o ícone com um pequeno delay para garantir que a janela foi criada pelo SO
        self.after(200,lambda: aplicar_icone_global(self))


# --- CLASSE RAIZ COM DND (Ajustada para garantir destruição) ---
class AppRoot(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        # Garante que ao fechar a janela principal, o processo morra
        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)

    def ao_fechar(self):
        try:
            self.quit()  # Para o mainloop
            self.destroy()  # Destroi a janela
        except:
            pass
        sys.exit()  # Força o encerramento do Python

# ==============================================================================
# CLASSE TOOLTIP SIMPLES
class CTkToolTip:
    # --- INICIALIZAÇÃO ---
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id_after = None # Variável para controlar o timer
        self.widget.bind("<Enter>", self.agendar_tooltip) # Mudou para agendar
        self.widget.bind("<Leave>", self.esconder_tooltip)
        self.widget.bind("<Button-1>", self.esconder_tooltip, add="+") # Esconde ao clicar

    # --- MÉTODOS DE EXIBIÇÃO E ESCONDER TOOLTIP ---
    def agendar_tooltip(self, event=None):
        # Cancela qualquer agendamento anterior
        self.esconder_tooltip()
        # Agenda a exibição para daqui a 500ms (meio segundo)
        self.id_after = self.widget.after(500, self.mostrar_tooltip)

    # --- MOSTRAR E ESCONDER TOOLTIP ---
    def mostrar_tooltip(self, event=None):
        if self.tooltip_window or not self.text: return
        
        # Posição ajustada (mais para baixo e direita para não cobrir o botão)
        x = self.widget.winfo_rootx() + 30 
        y = self.widget.winfo_rooty() + 30 
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Cria o rótulo
        label = tk.Label(tw, text=self.text, background="#2A2A2A", fg="white",
                         relief='solid', borderwidth=1, font=("Arial", 10))
        label.pack(ipadx=5, ipady=3)

    # --- ESCONDER TOOLTIP ---
    def esconder_tooltip(self, event=None):
        # Se houver um timer rodando, cancela ele (o mouse saiu antes dos 500ms)
        if self.id_after:
            self.widget.after_cancel(self.id_after)
            self.id_after = None
            
        # Se a janela já estiver aberta, fecha ela
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# ==============================================================================
# JANELAS AUXILIARES
# ==============================================================================
# --- DIÁLOGO DE FILTRO AVANÇADO ---
class FilterDialog(IconedToplevel):
    def __init__(self, parent, values, col_name, callback):
        super().__init__(parent)
        self.title(f"Filtrar: {col_name}")
        self.geometry("300x450")
        self.attributes('-topmost', True)
        self.callback = callback
        self.vars = {}
        self.entry_search = ctk.CTkEntry(self, placeholder_text="Buscar...")
        self.entry_search.pack(fill="x", padx=10, pady=5)
        self.entry_search.bind("<KeyRelease>", self.filter_list)
        self.var_all = ctk.StringVar(value="on")
        self.chk_all = ctk.CTkCheckBox(self, text="(Selecionar Todos)", variable=self.var_all, onvalue="on", offvalue="off", command=self.toggle_all)
        self.chk_all.pack(anchor="w", padx=10, pady=5)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)
        self.all_values = sorted(list(set(values)))
        self.create_checkboxes(self.all_values)
        ctk.CTkButton(self, text="Aplicar Filtro", fg_color="green", command=self.apply).pack(fill="x", padx=10, pady=10)
    def create_checkboxes(self, values):
        for w in self.scroll.winfo_children(): w.destroy()
        self.vars = {}
        for v in values:
            var = ctk.StringVar(value="on")
            self.vars[v] = var
            ctk.CTkCheckBox(self.scroll, text=str(v), variable=var, onvalue="on", offvalue="off").pack(anchor="w", pady=2)
    def filter_list(self, event):
        query = self.entry_search.get().lower()
        filtered = [v for v in self.all_values if query in str(v).lower()]
        self.create_checkboxes(filtered)
    def toggle_all(self):
        s = self.var_all.get(); [v.set(s) for v in self.vars.values()]
    def apply(self):
        selected = [k for k, v in self.vars.items() if v.get() == "on"]
        self.callback(selected); self.destroy()

# --- DIÁLOGO DE EXPORTAÇÃO ---
class DialogoExportacao(IconedToplevel):
    # --- DIÁLOGO DE EXPORTAÇÃO PARA EXCEL ---
    def __init__(self, parent, df_completo, janelas):
        super().__init__(parent)
        self.transient(parent); self.lift(); self.title("Exportar"); self.geometry("400x500")
        self.df = df_completo; self.janelas = janelas
        ctk.CTkLabel(self, text="Selecione as abas:", font=("Arial", 14, "bold")).pack(pady=10)
        self.scroll = ctk.CTkScrollableFrame(self); self.scroll.pack(fill="both", expand=True, padx=10)
        self.var_full = ctk.StringVar(value="on")
        ctk.CTkCheckBox(self.scroll, text="Base Completa (Bruta)", variable=self.var_full, onvalue="on", offvalue="off").pack(anchor="w")
        self.vars_j = {}
        for i, j in enumerate(janelas):
            if j.winfo_exists():
                v = ctk.StringVar(value="on")
                ctk.CTkCheckBox(self.scroll, text=f"Pivot #{j.id_dinamico}", variable=v, onvalue="on", offvalue="off").pack(anchor="w")
                self.vars_j[i] = v
        ctk.CTkButton(self, text="💾 Salvar Excel", fg_color="green", command=self.salvar).pack(pady=10)
    # --- AÇÃO DE SALVAR ---
    def salvar(self):
        f = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not f: return
        try:
            with pd.ExcelWriter(f, engine='openpyxl') as w:
                if self.var_full.get() == "on": self.df.to_excel(w, sheet_name="Base", index=False)
                for i, v in self.vars_j.items():
                    if v.get() == "on" and self.janelas[i].winfo_exists():
                        j = self.janelas[i]; valid = [c for c in j.df_orig.columns]
                        rows = [r for r in j.active_rows if r in valid]; cols = [c for c in j.active_cols if c in valid]
                        df = j.df_filtrado_cache
                        if rows:
                            if cols: p = pd.pivot_table(df, values="Valor", index=rows, columns=cols, aggfunc='sum')
                            else: p = df.groupby(rows)["Valor"].sum()
                            p.to_excel(w, sheet_name=f"Pivot_{j.id_dinamico}", merge_cells=True)
                        else: j.df_orig.to_excel(w, sheet_name=f"Pivot_{j.id_dinamico}", index=False)
            formatar_excel_como_tabela(f); messagebox.showinfo("OK", "Arquivo .xlsx Salvo!"); self.destroy(); os.startfile(f)
        except Exception as e: messagebox.showerror("Erro: feche o arquivo a ser substituído!", str(e))

# ==============================================================================
# VISUALIZADOR DINÂMICO (PIVOT)
# ==============================================================================
# --- JANELA DE ANÁLISE DINÂMICA ---
# ==============================================================================
# VISUALIZADOR DINÂMICO (PIVOT) - VERSÃO COMPLETA E CORRIGIDA
# ==============================================================================
class VisualizadorDinamico(IconedToplevel):
    # --- INICIALIZAÇÃO ---
    def __init__(self, parent, dataframe, index_id): 
        super().__init__(parent)
        
        # 1. Configurações de Janela (Invisível + Zoomed)
        self.attributes("-alpha", 0.0)
        self.attributes('-topmost', True)
        self.state('zoomed')
        
        # 2. Cores e Ícones
        self.colors = {
            "bg_window": "#2B2B2E",     # Fundo Geral
            "bg_sidebar": "#323235",    # Barra Lateral (estilo VS Code)
            "bg_card": "#2B2B2E",       # Cards (mesma cor do fundo para limpar)
            "primary": "#007ACC",       # Azul Principal
            "text_muted": "#858585"     # Texto secundário
        }
        self.configure(fg_color=self.colors["bg_window"])

        try:
            self.img_filter = tk.PhotoImage(data=ICON_FILTER_B64)
            self.img_up = tk.PhotoImage(data=ICON_UP_B64)
            self.img_down = tk.PhotoImage(data=ICON_DOWN_B64)
        except: self.img_filter = None; self.img_up = None; self.img_down = None

        # 3. Tratamento de Dados
        self.df_orig = dataframe.copy().fillna(0)
        if "Financiamento" in self.df_orig.columns:
            self.df_orig["Financiamento"] = self.df_orig["Financiamento"].astype(str).replace(
                ["MAC", "Média e Alta Complexidade", "Media e Alta Complexidade", "(MAC)"], "MAC"
            )
        if "Valor" in self.df_orig.columns:
            self.df_orig["Valor"] = pd.to_numeric(self.df_orig["Valor"], errors='coerce').fillna(0.0)
        for c in self.df_orig.columns:
            if c != "Valor": self.df_orig[c] = self.df_orig[c].astype(str)

        # 4. Variáveis de Estado
        self.id_dinamico = index_id
        self.df_filtrado_cache = self.df_orig.copy()
        self.cols_disponiveis = [c for c in self.df_orig.columns if c != "Valor"]
        self.cols_opcoes = self.cols_disponiveis
        self.active_rows = []; self.active_cols = []; self.active_filters = {}
        self.filtro_em_edicao = None; self.vars_filtro_temp = {}
        self.drag_data = {"item": None, "type": None}; self.widget_map_rows = {}; self.widget_map_cols = {}
        self.templates = self.carregar_templates(); self.quick_filter_hospital = None
        self.palettes = {"Black": ("#1E1E1E", "#3C3C3C"), 
                         "Dark": ("#181C1D", "#33556d"), 
                         "Floresta": ("#09311BFB", "#315740"),
                         "Cinzento": ("#2C2C2C", "#5A5A5A"), 
                         "Azul Escuro": ("#001F3F", "#003366")}
        tema_inicial = self.templates.get("_config_geral_", {}).get("ultimo_tema", "Dark")
        self.title(f"Análise Dinâmica #{index_id}")
        self.geometry("1300x800")

        # 5. ESTILO ISOLADO (CORREÇÃO DO ESPAÇAMENTO)
        style = ttk.Style()
        style.theme_use("clam")
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) 
        
        # Cria um estilo exclusivo "Pivot.Treeview" para NÃO afetar a janela de trás
        style.configure("Pivot.Treeview", background=self.colors["bg_card"], foreground="white", fieldbackground=self.colors["bg_card"], 
                        rowheight=30, borderwidth=0, font=("Segoe UI", 10))
        style.map("Pivot.Treeview", background=[('selected', self.colors["primary"])], foreground=[('selected', 'white')])
        
        style.configure("Pivot.Treeview.Heading", background="#353b48", foreground="white", relief="flat", font=("Segoe UI", 10, "bold"), padding=(10, 5))
        style.map("Pivot.Treeview.Heading", background=[('active', '#3d3d3d')])

        # 6. Layout Grid Principal
        self.grid_columnconfigure(0, weight=0, minsize=320)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=280)
        self.grid_rowconfigure(0, weight=0, minsize=60)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.on_voltar = None  # Definido externamente por quem abriu esta janela
        self.header_frame = ctk.CTkFrame(self, fg_color=self.colors["bg_sidebar"], corner_radius=0, height=60)
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.header_frame.grid_propagate(False)
        ctk.CTkButton(self.header_frame, text="< Voltar", font=("Segoe UI", 12), fg_color="transparent",
                      border_width=1, border_color="#505050", hover_color="#3E3E42",
                      width=90, height=32, command=self.voltar).pack(side="left", padx=(20, 10))
        ctk.CTkLabel(self.header_frame, text=f"ANÁLISE PIVOT #{index_id}", font=("Segoe UI", 20, "bold"), text_color=self.colors["primary"]).pack(side="left", padx=10)
        ctk.CTkButton(self.header_frame, text="📥 Exportar Excel", fg_color="#2980B9", font=("Segoe UI", 12, "bold"), width=140, height=35, command=self.exportar).pack(side="right", padx=20)

        # Sidebar Esquerda
        self.left_container = ctk.CTkFrame(self, fg_color=self.colors["bg_sidebar"], corner_radius=0)
        self.left_container.grid(row=1, column=0, sticky="nsew", padx=(0, 1), pady=(1, 0))
        self.sidebar = ctk.CTkScrollableFrame(self.left_container, fg_color="transparent")
        self.sidebar.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_section_header("MODELOS SALVOS")
        self.fr_templates_container = ctk.CTkFrame(self.sidebar, fg_color=self.colors["bg_card"], corner_radius=8)
        self.fr_templates_container.pack(fill="x", pady=(0, 10))
        self.render_template_area()

        self.create_section_header("CAMPOS DISPONÍVEIS")
        self.fr_fields_container = ctk.CTkFrame(self.sidebar, fg_color=self.colors["bg_card"], corner_radius=8)
        self.fr_fields_container.pack(fill="x", pady=(0, 10))
        self.scroll_fields = ctk.CTkScrollableFrame(self.fr_fields_container, height=180, fg_color="transparent")
        self.scroll_fields.pack(fill="both", expand=True, padx=2, pady=2)
        self.render_fields_list()

        self.create_section_header("LINHAS ≡")
        self.fr_rows_container = ctk.CTkFrame(self.sidebar, fg_color=self.colors["bg_card"], border_color="#3498DB", border_width=1, corner_radius=8)
        self.fr_rows_container.pack(fill="x", pady=(0, 10))
        self.fr_rows_list = ctk.CTkScrollableFrame(self.fr_rows_container, height=100, fg_color="transparent")
        self.fr_rows_list.pack(fill="both", expand=True)

        self.create_section_header("COLUNAS ||")
        self.fr_cols_container = ctk.CTkFrame(self.sidebar, fg_color=self.colors["bg_card"], border_color="#E67E22", border_width=1, corner_radius=8)
        self.fr_cols_container.pack(fill="x", pady=(0, 10))
        self.fr_cols_list = ctk.CTkScrollableFrame(self.fr_cols_container, height=80, fg_color="transparent")
        self.fr_cols_list.pack(fill="both", expand=True)

        self.create_section_header("FILTROS ATIVOS")
        self.fr_active_filters_container = ctk.CTkFrame(self.sidebar, fg_color=self.colors["bg_card"], corner_radius=8)
        self.fr_active_filters_container.pack(fill="x", pady=(0, 10))
        self.scroll_active_filters = ctk.CTkScrollableFrame(self.fr_active_filters_container, height=120, fg_color="transparent")
        self.scroll_active_filters.pack(fill="both", expand=True)

        # Centro (Tabela)
        self.center_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.center_container.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        self.status_bar = ctk.CTkFrame(self.center_container, fg_color=self.colors["bg_card"], height=40, corner_radius=8)
        self.status_bar.pack(fill="x", pady=(0, 10))
        self.lbl_msg = ctk.CTkLabel(self.status_bar, text="Carregando...", font=("Segoe UI", 14, "bold"), text_color="#F1C40F")
        self.lbl_msg.pack(side="left", padx=15, pady=8)
        ctk.CTkButton(self.status_bar, text="Recolher -", width=80, height=25, fg_color="#555", command=lambda: self.toggle_expand(False)).pack(side="right", padx=10, pady=8)
        ctk.CTkButton(self.status_bar, text="Expandir +", width=80, height=25, fg_color="#555", command=lambda: self.toggle_expand(True)).pack(side="right", padx=(0, 5), pady=8)

        self.tree_frame = ctk.CTkFrame(self.center_container, fg_color=self.colors["bg_card"], corner_radius=8)
        self.tree_frame.pack(fill="both", expand=True)
        
        # AQUI O USO DO ESTILO ISOLADO
        self.tree = ttk.Treeview(self.tree_frame, style="Pivot.Treeview")
        
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")
        self.tree_frame.grid_rowconfigure(0, weight=1); self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Button-3>", self.menu_contexto); self.tree.bind("<Double-1>", self.copiar_celula) 
        self.tree.bind("<Control-c>", lambda e: self.copiar_linha())

        # Sidebar Direita
        self.right_container = ctk.CTkFrame(self, fg_color=self.colors["bg_sidebar"], corner_radius=0)
        self.right_container.grid(row=1, column=2, sticky="nsew", padx=(1, 0), pady=(1, 0))
        self.scroll_right = ctk.CTkScrollableFrame(self.right_container, fg_color="transparent")
        self.scroll_right.pack(fill="both", expand=True, padx=5, pady=5)

        if "Hospital/Prestador" in self.cols_disponiveis:
            self.create_section_header("PRESTADORES (Filtro Rápido)", parent=self.scroll_right)
            self.fr_quick_container = ctk.CTkFrame(self.scroll_right, fg_color="transparent")
            self.fr_quick_container.pack(fill="x", pady=(0, 20))
            self.render_quick_filters()

        self.create_section_header("DETALHAR FILTRO", parent=self.scroll_right)
        self.fr_filter_edit = ctk.CTkFrame(self.scroll_right, fg_color=self.colors["bg_card"], corner_radius=8)
        self.fr_filter_edit.pack(fill="both", expand=True)
        self.cb_filtro = ctk.CTkComboBox(self.fr_filter_edit, values=["(Escolha)"] + self.cols_opcoes, command=self.carregar_interface_filtro, fg_color="#333", button_color="#444")
        self.cb_filtro.set("(Escolha)"); self.cb_filtro.pack(fill="x", padx=10, pady=10)
        self.scroll_filtros_opts = ctk.CTkScrollableFrame(self.fr_filter_edit, height=200, fg_color="transparent")
        self.scroll_filtros_opts.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkButton(self.fr_filter_edit, text="APLICAR FILTRO", fg_color=self.colors["primary"], command=self.aplicar_filtro_edicao, height=35).pack(fill="x", padx=10, pady=10)

        tema_salvo = self.templates.get("_config_geral_", {}).get("ultimo_tema", "Dark")
        self.create_section_header("APARÊNCIA (tabela)", parent=self.scroll_right)
        self.cb_theme = ctk.CTkComboBox(self.scroll_right, values=list(self.palettes.keys()), command=self.mudar_tema)
        self.cb_theme.set(tema_salvo); self.cb_theme.pack(fill="x", pady=(0, 20))

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Copiar Linha(s)", command=self.copiar_linha)
        self.menu.add_command(label="Expandir Tudo", command=lambda: self.toggle_expand(True))
        self.menu.add_command(label="Recolher Tudo", command=lambda: self.toggle_expand(False))
        self.menu.add_separator()
        self.menu.add_command(label="Exportar Excel", command=self.exportar)
        self.menu_header = tk.Menu(self, tearoff=0)

        # 7. Inicialização Final (Sem travar)
        if "Hospital/Prestador" in self.cols_disponiveis: self.add_to_active("Hospital/Prestador", "row")
        self.render_active_lists()
        
        # AGENDAMENTO DO CÁLCULO (Correção do travamento)
        self.after(200, self.iniciar_carregamento_seguro)

    # --- FUNÇÕES DE CARREGAMENTO SEGURO ---
    def iniciar_carregamento_seguro(self):
        try:
            self.calcular_pivot()
        except Exception as e:
            print(f"Erro no carregamento tardio: {e}")
        
        self.attributes('-topmost', False)
        self.animar_entrada()

    def animar_entrada(self):
        self.lift()
        self.focus_force()
        def step_fade(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.08
                self.attributes("-alpha", alpha)
                self.after(10, lambda: step_fade(alpha))
            else:
                self.attributes("-alpha", 1.0)
        step_fade()

    # --- FUNÇÕES AUXILIARES DE DESENHO E LÓGICA (RECUPERADAS) ---
    def create_section_header(self, text, parent=None):
        if parent is None: parent = self.sidebar
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 11, "bold"), text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 5))

    def render_template_area(self):
        for w in self.fr_templates_container.winfo_children(): w.destroy()
        frm_inner = ctk.CTkFrame(self.fr_templates_container, fg_color="transparent")
        frm_inner.pack(fill="both", expand=True, padx=5, pady=5)
        btn_save = ctk.CTkButton(frm_inner, text="+ NOVO MODELO", height=30, fg_color="transparent", border_width=1, border_color=self.colors["primary"], text_color=self.colors["primary"], hover_color="#333", command=self.gravar_template)
        btn_save.pack(fill="x", pady=(0, 10))
        self.scroll_templates = ctk.CTkScrollableFrame(frm_inner, height=150, fg_color="transparent", label_text="")
        self.scroll_templates.pack(fill="both", expand=True)
        self.atualizar_lista_templates_visual()

    def atualizar_lista_templates_visual(self):
        for w in self.scroll_templates.winfo_children(): w.destroy()
        for nome in self.templates.keys():
            if nome == "_config_geral_": continue
            f_item = ctk.CTkFrame(self.scroll_templates, fg_color="transparent"); f_item.pack(fill="x", pady=1)
            btn = ctk.CTkButton(f_item, text=nome, anchor="w", height=32, fg_color="transparent", hover_color="#404040", text_color="#E0E0E0", cursor="hand2", command=lambda n=nome: self.aplicar_template(n))
            btn.pack(side="left", fill="x", expand=True)
            btn_del = ctk.CTkButton(f_item, text="×", width=25, height=25, fg_color="transparent", hover_color="#C0392B", text_color="gray", cursor="hand2", command=lambda n=nome: self.excluir_template_por_nome(n))
            btn_del.pack(side="right", padx=2)

    def draw_chip(self, parent, text, idx, tipo):
        color = "#2980B9" if tipo == "row" else "#D35400"
        f = ctk.CTkFrame(parent, fg_color=self.colors["bg_window"], corner_radius=15, height=32)
        f.pack(fill="x", pady=2, padx=2)
        lbl_drag = ctk.CTkLabel(f, text="::", width=20, cursor="fleur", text_color="gray", font=("Arial", 12))
        lbl_drag.pack(side="left", padx=(8, 2))
        lbl_drag.bind("<Button-1>", lambda e, c=text, t=tipo: self.on_drag_start(e, c, t))
        lbl_drag.bind("<B1-Motion>", self.on_drag_motion); lbl_drag.bind("<ButtonRelease-1>", self.on_drag_drop)
        ctk.CTkLabel(f, text=text, font=("Segoe UI", 11)).pack(side="left", padx=5)
        btn_close = ctk.CTkButton(f, text="×", width=24, height=24, fg_color="transparent", hover_color="#C0392B", corner_radius=12, command=lambda: self.remove_active(text, tipo))
        btn_close.pack(side="right", padx=2)
        if tipo == "row": self.widget_map_rows[f] = text
        else: self.widget_map_cols[f] = text

    def draw_filter_card(self, col, values):
        f = ctk.CTkFrame(self.scroll_active_filters, fg_color=self.colors["bg_window"], corner_radius=6)
        f.pack(fill="x", pady=2, padx=2)
        head = ctk.CTkFrame(f, fg_color="transparent", height=20); head.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(head, text=col, font=("Segoe UI", 11, "bold"), text_color="#F39C12").pack(side="left")
        ctk.CTkButton(head, text="✕", width=20, height=20, fg_color="transparent", hover_color="#C0392B", cursor="hand2", text_color="red", command=lambda: self.remove_filter(col)).pack(side="right")
        btn_edit = ctk.CTkButton(head, text="⚙", width=24, height=24, font=("Arial", 14), text_color="#00BFFF", fg_color="transparent", hover_color="#2B2B2B", cursor="hand2", corner_radius=6, command=lambda: self.abrir_edicao_filtro(col))
        btn_edit.pack(side="right", padx=2)
        total = len(self.df_orig[col].unique()); sel = len(values)
        resumo = "(Todos)" if sel == total else (", ".join(list(values)[:3]) if sel <= 3 else f"{', '.join(list(values)[:2])} (+{sel - 2})")
        ctk.CTkLabel(f, text=resumo, font=("Segoe UI", 10), text_color="gray", anchor="w").pack(fill="x", padx=8, pady=(0, 5))

    def render_fields_list(self):
        for w in self.scroll_fields.winfo_children(): w.destroy()
        for col in self.cols_disponiveis:
            f = ctk.CTkFrame(self.scroll_fields, fg_color="transparent", height=28); f.pack(fill="x", pady=1)
            ctk.CTkLabel(f, text=col[:28], anchor="w", font=("Segoe UI", 11), text_color="#ddd").pack(side="left", padx=2)
            ctk.CTkButton(f, text="Y", width=24, height=24, fg_color="#333", hover_color="#F39C12", command=lambda c=col: self.add_filter(c)).pack(side="right", padx=1)
            ctk.CTkButton(f, text="||", width=24, height=24, fg_color="#333", hover_color="#E67E22", command=lambda c=col: self.add_to_active(c, "col")).pack(side="right", padx=1)
            ctk.CTkButton(f, text="≡", width=24, height=24, fg_color="#333", hover_color="#3498DB", command=lambda c=col: self.add_to_active(c, "row")).pack(side="right", padx=1)

    def mudar_tema(self, event=None):
        novo_tema = self.cb_theme.get()
        if "_config_geral_" not in self.templates: self.templates["_config_geral_"] = {}
        self.templates["_config_geral_"]["ultimo_tema"] = novo_tema
        try:
            with open("templates.json", "w", encoding="utf-8") as f: json.dump(self.templates, f, indent=4, ensure_ascii=False)
        except: pass
        self.calcular_pivot()

    def render_quick_filters(self):
        for w in self.fr_quick_container.winfo_children(): w.destroy()
        hospitais = sorted(list(self.df_orig["Hospital/Prestador"].unique()))
        for hosp in hospitais:
            is_active = (self.quick_filter_hospital == hosp)
            color = self.colors["primary"] if is_active else "transparent"
            text_col = "white" if is_active else "gray"
            border = 0 if is_active else 1
            btn = ctk.CTkButton(self.fr_quick_container, text=hosp[:35], fg_color=color, border_color="gray", border_width=border, text_color=text_col, anchor="w", height=24, font=("Segoe UI", 11), command=lambda h=hosp: self.toggle_quick_filter(h))
            btn.pack(fill="x", pady=2)
            if len(hosp) > 35: CTkToolTip(btn, hosp)

    def toggle_quick_filter(self, hospital):
        if self.quick_filter_hospital == hospital:
            self.quick_filter_hospital = None
            if "Hospital/Prestador" in self.active_filters: del self.active_filters["Hospital/Prestador"]
        else:
            self.quick_filter_hospital = hospital
            self.active_filters["Hospital/Prestador"] = {hospital}
        self.reset_interface_filtro(); self.render_active_lists(); self.render_quick_filters(); self.calcular_pivot()

    # --- INTERFACE DE EDIÇÃO DE FILTRO DETALHADO ---
    def carregar_interface_filtro(self, col):
        for w in self.scroll_filtros_opts.winfo_children(): w.destroy()
        self.vars_filtro_temp = {}; self.filtro_em_edicao = col
        if col == "(Escolha)": return
        todos = sorted(list(self.df_orig[col].unique()))
        ativos = self.active_filters.get(col, set(todos))
        var_all = ctk.StringVar(value="on")
        chk_all = ctk.CTkCheckBox(self.scroll_filtros_opts, text="(Todos)", variable=var_all, onvalue="on", offvalue="off", command=lambda: self.toggle_all(var_all))
        chk_all.pack(anchor="w", pady=2)
        for val in todos:
            st = "on" if val in ativos else "off"
            v = ctk.StringVar(value=st)
            self.vars_filtro_temp[str(val)] = v
            ctk.CTkCheckBox(self.scroll_filtros_opts, text=str(val), variable=v, onvalue="on", offvalue="off", command=lambda: self.verificar_estado_todos(var_all)).pack(anchor="w", pady=2)
        self.verificar_estado_todos(var_all)
    
    def toggle_all(self, mv): 
        s = mv.get()
        for v in self.vars_filtro_temp.values(): v.set(s)
            
    def verificar_estado_todos(self, var_all):
        valores = [v.get() for v in self.vars_filtro_temp.values()]
        if "off" in valores: var_all.set("off")
        else: var_all.set("on")

    def reset_interface_filtro(self):
        self.cb_filtro.set("(Escolha)")
        for w in self.scroll_filtros_opts.winfo_children(): w.destroy()
        self.vars_filtro_temp = {}
        self.filtro_em_edicao = None

    def header_click(self, col):
        self.menu_header.delete(0, "end")
        self.menu_header.add_command(label="🔼 Classificar A-Z", command=lambda: self.sort_tree(col, False))
        self.menu_header.add_command(label="🔽 Classificar Z-A", command=lambda: self.sort_tree(col, True))
        self.menu_header.add_separator()
        self.menu_header.add_command(label="🔍 Filtrar Valores...", command=lambda: self.open_header_filter(col))
        x, y = self.winfo_pointerx(), self.winfo_pointery(); self.menu_header.post(x, y)

    def sort_tree(self, col, reverse):
        def sort_node(parent_item):
            children = self.tree.get_children(parent_item)
            if not children: return
            sort_list = []
            for child in children:
                val = self.tree.item(child, "text") if col == "#0" else self.tree.set(child, col)
                try: clean_val = float(val.replace("R$ ", "").replace(".", "").replace(",", ".") if isinstance(val, str) else val)
                except: clean_val = str(val)
                sort_list.append((clean_val, child))
            sort_list.sort(key=lambda x: x[0], reverse=reverse)
            for index, (_, child_id) in enumerate(sort_list):
                self.tree.move(child_id, parent_item, index)
                sort_node(child_id)
        sort_node("")
        for c in self.tree["columns"]: self.tree.heading(c, image='')
        self.tree.heading("#0", image=''); target = self.img_down if reverse else self.img_up
        self.tree.heading(col, image=target)

    def open_header_filter(self, col):
        values = []
        def get_vals(parent):
            for item in self.tree.get_children(parent):
                values.append(self.tree.item(item, "text") if col == "#0" else self.tree.set(item, col))
                get_vals(item)
        get_vals("")
        FilterDialog(self, values, col, lambda sel: self.apply_local_filter(col, sel))

    def apply_local_filter(self, col, selected):
        self.calcular_pivot()
        def filter_node(parent):
            for item in self.tree.get_children(parent):
                val = self.tree.item(item, "text") if col == "#0" else self.tree.set(item, col)
                if val not in selected: self.tree.detach(item)
                else: filter_node(item)
        filter_node("")
        if self.img_filter: self.tree.heading(col, image=self.img_filter)

    def toggle_expand(self, open_all):
        def r(item):
            self.tree.item(item, open=open_all)
            for c in self.tree.get_children(item): r(c)
        for c in self.tree.get_children(): r(c)
    
    def render_active_lists(self):
        for w in self.fr_rows_list.winfo_children(): w.destroy()
        self.widget_map_rows = {}
        for idx, col in enumerate(self.active_rows): self.draw_chip(self.fr_rows_list, col, idx, "row")
        for w in self.fr_cols_list.winfo_children(): w.destroy()
        self.widget_map_cols = {}
        for idx, col in enumerate(self.active_cols): self.draw_chip(self.fr_cols_list, col, idx, "col")
        for w in self.scroll_active_filters.winfo_children(): w.destroy()
        if not self.active_filters: ctk.CTkLabel(self.scroll_active_filters, text="Clique em 'Y' na lista de opções.", text_color="gray", font=("Segoe UI", 10)).pack(pady=5)
        for col, values in self.active_filters.items(): self.draw_filter_card(col, values)

    def on_drag_start(self, event, col, tipo):
        self.drag_data["item"] = col; self.drag_data["type"] = tipo; self.configure(cursor="fleur")
    
    def on_drag_motion(self, event): pass
    
    def on_drag_drop(self, event):
        self.configure(cursor=""); orig, tipo = self.drag_data["item"], self.drag_data["type"]
        if not orig: return
        y = self.winfo_pointery()
        w_map = self.widget_map_rows if tipo == "row" else self.widget_map_cols
        lista = self.active_rows if tipo == "row" else self.active_cols
        dest = None
        for w, name in w_map.items():
            if w.winfo_rooty() <= y <= w.winfo_rooty() + w.winfo_height(): dest = name; break
        if dest and dest != orig:
            i1, i2 = lista.index(orig), lista.index(dest); lista.pop(i1); lista.insert(i2, orig)
            self.render_active_lists(); self.calcular_pivot()
        self.drag_data = {"item": None, "type": None}

    def carregar_templates(self):
        defaults = {}
        try:
            if os.path.exists("templates.json"):
                with open("templates.json", "r", encoding="utf-8") as f: defaults.update(json.load(f))
        except: pass
        if not defaults: defaults = {"1. Resumo": {"rows": ["Hospital/Prestador"], "cols": []}}
        return defaults

    def gravar_template(self):
        dialog = IconedToplevel(self)
        dialog.title("Salvar Modelo")
        dialog.geometry("350x180")
        dialog.attributes('-topmost', True)
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + (self.winfo_height() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        ctk.CTkLabel(dialog, text="Nome do novo modelo:", font=("Segoe UI", 12, "bold")).pack(pady=(20, 5))
        entry = ctk.CTkEntry(dialog, width=250); entry.pack(pady=5); entry.focus()
        def confirmar():
            nome = entry.get().strip()
            if not nome: return
            filtros_salvar = {k: list(v) for k, v in self.active_filters.items()}
            self.templates[nome] = {"rows": self.active_rows, "cols": self.active_cols, "filters": filtros_salvar}
            self.atualizar_lista_templates_visual()
            try:
                with open("templates.json", "w", encoding="utf-8") as f: json.dump(self.templates, f, indent=4, ensure_ascii=False)
                dialog.destroy() 
                messagebox.showinfo("Sucesso", "Modelo salvo com sucesso!", parent=self)
            except Exception as e:
                if dialog.winfo_exists(): messagebox.showerror("Erro", str(e), parent=dialog)
                else: messagebox.showerror("Erro", str(e), parent=self)
        ctk.CTkButton(dialog, text="Salvar", command=confirmar, fg_color=self.colors["primary"]).pack(pady=20)
        dialog.bind('<Return>', lambda e: confirmar())

    def menu_contexto_templates(self, event): pass
    
    def excluir_template_por_nome(self, nome):
        if messagebox.askyesno("Confirmar", f"Deseja excluir o modelo '{nome}'?", parent=self):
            if nome in self.templates:
                del self.templates[nome]
                try:
                    with open("templates.json", "w", encoding="utf-8") as f: json.dump(self.templates, f, indent=4, ensure_ascii=False)
                    self.atualizar_lista_templates_visual()
                except: pass

    def aplicar_template(self, nome):
        cfg = self.templates.get(nome)
        if not cfg: return
        self.active_rows = [r for r in cfg["rows"] if r in self.cols_disponiveis]
        self.active_cols = [c for c in cfg["cols"] if c in self.cols_disponiveis]
        self.active_filters = {}
        raw_filtros = cfg.get("filters", {})
        for k, v in raw_filtros.items():
            if k in self.df_orig.columns: self.active_filters[k] = set(v)
        self.reset_interface_filtro(); self.quick_filter_hospital = None
        self.render_quick_filters(); self.render_active_lists(); self.calcular_pivot()

    def add_to_active(self, col, tipo):
        if tipo == "row":
            if col not in self.active_rows: self.active_rows.append(col)
            if col in self.active_cols: self.active_cols.remove(col)
        else:
            if col not in self.active_cols: self.active_cols.append(col)
            if col in self.active_rows: self.active_rows.remove(col)
        self.render_active_lists(); self.calcular_pivot()

    def remove_active(self, col, tipo):
        try:
            if tipo == "row": self.active_rows.remove(col)
            else: self.active_cols.remove(col)
            self.render_active_lists(); self.calcular_pivot()
        except: pass
    
    def add_filter(self, col):
        if col not in self.active_filters: self.active_filters[col] = set(self.df_orig[col].unique())
        self.render_active_lists(); self.abrir_edicao_filtro(col)
    
    def abrir_edicao_filtro(self, col): self.cb_filtro.set(col); self.carregar_interface_filtro(col) 
    
    def aplicar_filtro_edicao(self):
        if not self.filtro_em_edicao: return
        sel = set()
        for v, var in self.vars_filtro_temp.items():
            if var.get() == "on": sel.add(v)
        self.active_filters[self.filtro_em_edicao] = sel
        self.render_active_lists(); self.calcular_pivot()
    
    def remove_filter(self, col):
        if col in self.active_filters: del self.active_filters[col]
        if col == "Hospital/Prestador": self.quick_filter_hospital = None; self.render_quick_filters()
        self.reset_interface_filtro(); self.render_active_lists(); self.calcular_pivot()

    def calcular_pivot(self):
        self.lbl_msg.configure(text="", text_color="yellow"); self.update_idletasks()
        try:
            df = self.df_orig.copy()
            for col, allowed in self.active_filters.items():
                if col in df.columns: df = df[df[col].isin(allowed)]
            self.df_filtrado_cache = df
            if not self.active_rows:
                self.tree.delete(*self.tree.get_children()); self.tree["columns"] = (); self.tree["displaycolumns"] = ()
                self.lbl_msg.configure(text=f"Total Geral: R$ {df['Valor'].sum():,.2f}", text_color=self.colors["primary"]); return
            if set(self.active_rows).intersection(set(self.active_cols)):
                self.lbl_msg.configure(text="Erro: Coluna repetida.", text_color="red"); return
            if not self.active_cols:
                piv = df.groupby(self.active_rows)["Valor"].sum().reset_index(); d_cols = ["Valor"]
            else:
                piv = pd.pivot_table(df, values="Valor", index=self.active_rows, columns=self.active_cols, aggfunc='sum', fill_value=0)
                piv['Total'] = piv.sum(axis=1); piv = piv.reset_index()
                d_cols = [c for c in piv.columns if c not in self.active_rows]
                        # Converte MultiIndex para String legível "Nível1 - Nível2"
            new_cols = []
            for c in piv.columns:
                if isinstance(c, tuple):
                    # Remove níveis vazios e junta com " - "
                    new_cols.append(" - ".join([str(x) for x in c if x]))
                else:
                    new_cols.append(str(c))

            piv.columns = new_cols
            # Atualiza a lista d_cols removendo as linhas ativas (index)
            d_cols = [c for c in piv.columns if c not in self.active_rows]


            self.df_pivotado = piv
            self.tree.delete(*self.tree.get_children())
            for c in self.tree["columns"]: self.tree.heading(c, image='') 
            self.tree.heading("#0", image='') 
            self.tree["displaycolumns"] = ()
            self.tree["columns"] = d_cols
            self.tree["displaycolumns"] = d_cols 

            # AUTO-FIT E ESTILO
            h_font = Font(family="Segoe UI", size=10, weight="bold")
            txt_rows = " / ".join(self.active_rows)
            w_rows = max(400, h_font.measure(txt_rows) + 40)
            self.tree.column("#0", width=w_rows, minwidth=400, anchor="w", stretch=True)
            self.tree.heading("#0", text=txt_rows, anchor="w", command=lambda: self.header_click("#0"))

            for c in d_cols:
                self.tree.heading(c, text=c, anchor="e", command=lambda col=c: self.header_click(col))
                txt_width = h_font.measure(c) + 25
                final_width = max(120, txt_width)
                self.tree.column(c, width=final_width, minwidth=100, anchor="e", stretch=False)

            selected_theme = self.cb_theme.get()
            colors = self.palettes.get(selected_theme, ("#2d3436", "#1e272e"))
            def hex_to_rgb(hex_col): return tuple(int(hex_col.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            def rgb_to_hex(rgb): return '#{:02x}{:02x}{:02x}'.format(*rgb)
            def interp(s_hex, e_hex, steps, step):
                s, e = hex_to_rgb(s_hex), hex_to_rgb(e_hex)
                r = int(s[0] + (e[0] - s[0]) * step / max(1, steps))
                g = int(s[1] + (e[1] - s[1]) * step / max(1, steps))
                b = int(s[2] + (e[2] - s[2]) * step / max(1, steps))
                return rgb_to_hex((r, g, b))
            max_d = len(self.active_rows)
            for i in range(max_d + 1):
                bg = interp(colors[0], colors[1], max_d, i); fg = "white"
                self.tree.tag_configure(f"level_{i}", background=bg, foreground=fg)
            def fmt(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            def ins(p, sub, lvls, d):
                if not lvls: return
                lvl = lvls[0]; grps = []
                for n, g in sub.groupby(lvl):
                    s = g[d_cols].sum(); t = s.sum() if hasattr(s, 'sum') else s
                    grps.append((t, n, g, s))
                grps.sort(key=lambda x: x[0], reverse=True)
                for _, n, g, s in grps:
                    vs = []
                    for c in d_cols:
                        try: vs.append(fmt(s[c]))
                        except: vs.append("0,00")
                    nd = self.tree.insert(p, "end", text=str(n), values=vs, open=True, tags=(f"level_{d}",))
                    ins(nd, g, lvls[1:], d + 1)
            ins("", piv, self.active_rows, 0)
            self.lbl_msg.configure(text=f"Total Processado: R$ {self.df_filtrado_cache['Valor'].sum():,.2f}", text_color="#2ECC71")
        except Exception as e: messagebox.showerror("Erro", str(e))
    
    def menu_contexto(self, e):
        r = self.tree.identify_region(e.x, e.y)
        if r == "heading": c = self.tree.identify_column(e.x); txt = "#0" if c == "#0" else self.tree.heading(c, "text"); self.header_click(txt)
        else: self.menu.post(e.x_root, e.y_root)
    
    def copiar_linha(self):
        selection = self.tree.selection();
        if not selection: return
        rows = []
        for i in selection: t = self.tree.item(i, "text"); v = self.tree.item(i, "values"); rows.append(f"{t}\t" + "\t".join(map(str, v)))
        self.clipboard_clear(); self.clipboard_append("\n".join(rows))
    
    def exportar(self): DialogoExportacao(self, self.df_orig, [self])
    
    def copiar_celula(self, e):
        r = self.tree.identify("region", e.x, e.y) 
        if r not in ["cell", "tree"]: return
        i = self.tree.identify_row(e.y)
        if not i: return
        caminho_hierarquia = []
        curr = i
        while curr:
            texto = self.tree.item(curr, "text")
            if texto: caminho_hierarquia.insert(0, texto)
            curr = self.tree.parent(curr)
        rotulo_final = " \n ".join(caminho_hierarquia) if caminho_hierarquia else "Valor"
        valor_celula = ""
        if r == "tree": valor_celula = self.tree.item(i, "text")
        elif r == "cell":
            c = self.tree.identify_column(e.x)
            nome_coluna = self.tree.heading(c, "text")
            rotulo_final += f" - {nome_coluna}"
            try:
                idx = int(c.replace("#", "")) - 1
                vs = self.tree.item(i, "values")
                if idx < len(vs): valor_celula = vs[idx]
            except: pass
        if valor_celula:
            top = IconedToplevel(self)
            top.title("Copiar")
            top.geometry("350x160")
            top.attributes('-topmost', True)
            top.geometry(f"+{e.x_root - 175}+{e.y_root - 80}")
            def fechar(e): top.after(10, check_focus)
            def check_focus():
                focused = top.focus_get()
                if focused is None or (hasattr(focused, 'winfo_toplevel') and focused.winfo_toplevel() != top): top.destroy()
            top.bind("<FocusOut>", fechar); top.focus_force()
            ctk.CTkLabel(top, text=rotulo_final, font=("Segoe UI", 11, "bold"), text_color="#F39C12").pack(pady=(15, 5))
            ent = ctk.CTkEntry(top, width=300, justify="center"); ent.pack(pady=5, padx=20)
            ent.insert(0, str(valor_celula)); ent.select_range(0, 'end'); ent.focus()
            ctk.CTkLabel(top, text="(Ctrl+C para copiar)", font=("Segoe UI", 10), text_color="gray").pack(pady=5)
        return "break"




class VisualizadorCompleto(IconedToplevel):
    def __init__(self, parent, df):
        super().__init__(parent)
        self.df = df
        self.janelas = []
        self.title("Dados Brutos")
        self.geometry("1100x600")
        
        # --- CONFIGURAÇÃO DE ESTILO (SaaS Dark Mode) ---
        # Fundo do Treeview mais sóbrio
        style = ttk.Style()
        style.theme_use("clam")
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        style.configure("Treeview", background="#2B2B2E", foreground="#E0E0E0", fieldbackground="#2B2B2E", rowheight=30, borderwidth=0)
        style.map("Treeview", background=[('selected', '#264F78')], foreground=[('selected', 'white')]) # Azul VS Code
        style.configure("Treeview.Heading", background="#323235", foreground="#CCCCCC", relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview.Heading", background=[('active', '#3E3E42')])

        # --- CABEÇALHO "SaaS" (Minimalista) ---
        self.on_voltar = None  # Definido externamente por quem abriu esta janela
        self.frm_header = ctk.CTkFrame(self, height=60, fg_color="#323235") # Cor de barra de ferramentas
        self.frm_header.pack(fill="x")
        self.frm_header.pack_propagate(False)

        # 0. Botão Voltar (navegação de ida e volta entre as telas)
        self.btn_voltar = ctk.CTkButton(
            self.frm_header, text="< Voltar", font=("Segoe UI", 12),
            fg_color="transparent", border_width=1, border_color="#505050",
            hover_color="#3E3E42", width=90, height=32, corner_radius=6,
            command=self.voltar
        )
        self.btn_voltar.pack(side="left", padx=(15, 5))

        # 1. Título Limpo
        lbl_titulo = ctk.CTkLabel(self.frm_header, text="Análise de Dados", font=("Segoe UI", 16, "bold"), text_color="white")
        lbl_titulo.pack(side="left", padx=10)
        
        # 2. Container BLINDADO (Lado Direito)
        fr_botoes = ctk.CTkFrame(self.frm_header, fg_color="transparent", width=420, height=40)
        fr_botoes.pack(side="right", padx=15)
        fr_botoes.pack_propagate(False) 
        
        # --- BOTÕES MODERNOS (Sem Emojis, Cores Corporativas) ---
        
        # Botão 1: Histórico (Secundário - Cinza)
        self.btn_hist = ctk.CTkButton(
            fr_botoes, 
            text="Adicionar ao Histórico",  # Texto formal
            font=("Segoe UI", 12),
            fg_color="#3E3E42",           # Cinza Escuro (Visual Studio style)
            hover_color="#505050",
            width=140, height=32,
            corner_radius=6,
            command=lambda: [self.destacar_botao(self.btn_hist), self.adicionar_serie_historica()]
        )
        self.btn_hist.place(x=0, rely=0.5, anchor="w")

        # Botão 2: Pivot (PRINCIPAL - Azul Enterprise)
        self.btn_dinamica = ctk.CTkButton(
            fr_botoes, 
            text="Tabela Dinâmica", 
            font=("Segoe UI", 12, "bold"),
            fg_color="#007ACC",           # Azul Profissional (Brand Color)
            hover_color="#0063A5",
            width=140, height=32,
            corner_radius=6,
            command=lambda: [self.destacar_botao(self.btn_dinamica), self.nova()]
        )
        self.btn_dinamica.place(x=150, rely=0.5, anchor="w")

        # Botão 3: Exportar (Terciário - Outline/Ghost)
        self.btn_exp = ctk.CTkButton(
            fr_botoes, 
            text="Exportar Excel", 
            font=("Segoe UI", 12),
            fg_color="transparent",       # Fundo transparente
            border_width=1,               # Borda fina
            border_color="#505050",       # Cor da borda
            hover_color="#2D2D30",
            width=110, height=32,
            corner_radius=6,
            command=lambda: [self.destacar_botao(self.btn_exp), self.exportar()]
        )
        self.btn_exp.place(x=300, rely=0.5, anchor="w")        # ----------------------------------------------------

        # Container e Treeview (O resto continua igual...)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=0) # Remove padding para colar nas bordas
        
        self.tree = ttk.Treeview(container, show="headings")
        # ... (Continue o código original daqui para baixo: binds, scrollbars, loops de dados)
        # Se precisar do resto do __init__ me avise, mas é só manter o que você já tinha.
        
        # Binds de Eventos (Clique Direito adicionado aqui)
        self.tree.bind("<Button-3>", self.abrir_menu_contexto)
        
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Lógica de Colunas (Auto-Fit)
        cols = list(df.columns)
        self.tree["columns"] = cols
        
        h_font = Font(family="Segoe UI", size=10, weight="bold")
        d_font = Font(family="Segoe UI", size=9)
        amostra = df.head(100)
        permitir_esticar = len(cols) < 6 

        for c in cols:
            w_header = h_font.measure(c) + 30
            w_data = 0
            if not amostra.empty:
                def get_formatted_len(val):
                    txt = str(val)
                    if c == "Valor" and isinstance(val, (int, float)):
                        txt = f"R$ {val:,.2f}"
                    return d_font.measure(txt)
                w_data = max([get_formatted_len(v) for v in amostra[c]]) + 20

            final_width = max(100, w_header, w_data)
            self.tree.heading(c, text=c, command=lambda col=c: self.header_click(col))
            self.tree.column(c, width=final_width, minwidth=100, stretch=permitir_esticar)
            
        self.menu_header = tk.Menu(self, tearoff=0)
        
        # Menu de Contexto (Clique Direito)
        self.menu_ctx = tk.Menu(self, tearoff=0)
        
        # Insere dados
        for _, r in df.head(2000).iterrows():
            vals = []
            for col_name, val in r.items():
                if col_name == "Valor" and isinstance(val, (int, float)): 
                    vals.append(f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                else: 
                    vals.append(val)
            self.tree.insert("", "end", values=vals)
    
    # --- VOLTAR PARA A TELA ANTERIOR ---
    def voltar(self):
        if self.on_voltar:
            self.on_voltar()
        else:
            self.destroy()

    # --- NOVO: Lógica de Destaque dos Botões ---
    # NA CLASSE VisualizadorCompleto
    def destacar_botao(self, botao_selecionado):
        # 1. Limpa o visual de todos (Estado Normal)
        self.btn_hist.configure(border_width=0)
        
        # CORREÇÃO: Removemos o 'border_color="transparent"' que causava o erro
        self.btn_dinamica.configure(border_width=0) 
        
        self.btn_exp.configure(border_width=1, border_color="#505050") 
        
        # 2. Aplica o destaque no clicado (Estado Ativo)
        if botao_selecionado == self.btn_exp:
            botao_selecionado.configure(border_width=1, border_color="#FFFFFF") 
        else:
            botao_selecionado.configure(border_width=2, border_color="#FFFFFF")

    # --- NOVO: Lógica do Menu de Contexto ---
    def abrir_menu_contexto(self, event):
        # Limpa menu anterior
        self.menu_ctx.delete(0, "end")
        
        # Identifica onde clicou
        iid = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        
        if not iid: return # Clicou fora

        # Seleciona a linha clicada (visual)
        self.tree.selection_set(iid)

        # Descobre valor e nome da coluna
        col_idx = int(col_id.replace("#", "")) - 1
        col_name = self.tree["columns"][col_idx]
        vals = self.tree.item(iid, "values")
        valor_celula = vals[col_idx] if col_idx < len(vals) else ""

        # Monta o Menu
        self.menu_ctx.add_command(label=f"📋 Copiar: '{str(valor_celula)[:20]}...'", 
                                command=lambda: self.copiar_texto(valor_celula))
        
        self.menu_ctx.add_command(label="📑 Copiar Linha Inteira", 
                                command=lambda: self.copiar_texto("\t".join(map(str, vals))))
        
        self.menu_ctx.add_separator()
        
        self.menu_ctx.add_command(label=f"🔍 Filtrar por: {str(valor_celula)[:15]}...", 
                                command=lambda: self.filtro_rapido(col_name, valor_celula))
        
        self.menu_ctx.add_command(label="❌ Remover Filtros desta Coluna", 
                                command=lambda: self.apply_filter(col_name, [])) # Lista vazia = reset no filtro lógico

        # Mostra o menu
        self.menu_ctx.post(event.x_root, event.y_root)

    ############ Funções de Menu de Contexto ############
    def copiar_texto(self, texto):
        self.clipboard_clear()
        self.clipboard_append(str(texto))

    #  Função de Filtro Rápido  
    def filtro_rapido(self, col, valor):
        # Reutiliza a função de filtro existente, passando apenas o valor clicado
        self.apply_filter(col, [valor])
    # ----------------------------------------

    ############ FIM Funções de Menu de Contexto ############
    def header_click(self, col):
        self.menu_header.delete(0, "end")
        self.menu_header.add_command(label="🔼 Classificar A-Z", command=lambda: self.sort_col(col, False))
        self.menu_header.add_command(label="🔽 Classificar Z-A", command=lambda: self.sort_col(col, True))
        self.menu_header.add_separator()
        self.menu_header.add_command(label="🔍 Filtrar...", command=lambda: self.filter_col(col))
        x, y = self.winfo_pointerx(), self.winfo_pointery()
        self.menu_header.post(x, y)

    # --- ORDENA COLUNA ---
    def sort_col(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try: l.sort(key=lambda t: float(t[0].replace("R$ ", "").replace(".", "").replace(",", ".")), reverse=reverse)
        except: l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l): self.tree.move(k, '', index)
        for c in self.tree["columns"]: self.tree.heading(c, image='')
        img = self.img_down if reverse else self.img_up
        self.tree.heading(col, image=img)

    # --- ABRE DIÁLOGO DE FILTRO ---
    def filter_col(self, col): 
        values = [self.tree.set(k, col) for k in self.tree.get_children('')]
        FilterDialog(self, values, col, lambda sel: self.apply_filter(col, sel))
    
    # --- APLICA FILTRO LÓGICO ---
    def apply_filter(self, col, selected):
        # Se a lista 'selected' estiver vazia, significa "Limpar Filtro"
        if not selected:
            # 1. Remove o ícone de funil do cabeçalho
            self.tree.heading(col, image='')
            
            # 2. Limpa a tabela atual (que está com dados ocultos)
            self.tree.delete(*self.tree.get_children())
            
            # 3. Recarrega os dados originais do DataFrame (self.df)
            # Isso traz de volta tudo o que estava escondido
            for _, r in self.df.head(2000).iterrows():
                vals = []
                for col_name, val in r.items():
                    if col_name == "Valor" and isinstance(val, (int, float)): 
                        vals.append(f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    else: 
                        vals.append(val)
                self.tree.insert("", "end", values=vals)
            return

        # --- Lógica de Filtrar (Esconder o que não foi selecionado) ---
        self.tree.heading(col, image=self.img_filter)
        
        to_del = []
        for k in self.tree.get_children(''):
            val = self.tree.set(k, col)
            if val not in selected: 
                to_del.append(k)
        
        # O detach apenas "esconde" da visualização
        for k in to_del: self.tree.detach(k)

    
    # --- ABRE NOVA JANELA DE TABELA DINÂMICA (CORRIGIDO: SEM TRAVAMENTO/ZOOM) ---
        # Na classe VisualizadorCompleto (Dados Brutos)
    
    # --- SUBSTITUA A FUNÇÃO 'nova' POR ESTE BLOCO COMPLETO ---
    # --- VERSÃO FINAL: SEM "PULINHO" NA TELA ---

    # Na classe VisualizadorCompleto
    
    # --- VERSÃO FINAL: SEM MEXER A JANELA ---
    # --- LÓGICA PERFEITA: AMPULHETA + SEM PULO + BOTÃO SOLTO ---
    # --- NOVO MÉTODO: MODO "FOCO TOTAL" ---
    # --- VERSÃO DEFINITIVA: AMPULHETA + MODO FOCO (ESCONDE JANELA) ---
    # --- VERSÃO CORRIGIDA: A AMPULHETA APARECE ANTES DE SUMIR ---
    # --- VERSÃO SEM FLET: APENAS TKINTER ---
    def nova(self):
        # 1. Muda cursor para ampulheta
        self.configure(cursor="watch")
        self.btn_dinamica.configure(cursor="watch")
        
        # 2. Força atualização visual (para você ver a ampulheta)
        self.update_idletasks()
        
        # 3. Agenda a abertura
        self.after(50, self._executar_abertura)

    def _executar_abertura(self):
        try:
            # Cria a janela filha
            win = VisualizadorDinamico(self, self.df.copy(), len(self.janelas) + 1)
            self.janelas.append(win)
            
            # ESCONDE A JANELA MÃE (Modo Foco)
            self.withdraw()
            
            # Configura o retorno quando fechar a filha
            def ao_fechar_dinamica():
                win.destroy()       
                self.deiconify()    # REAPARECE A MÃE
                self.lift()         
                self.focus_force()
                self.configure(cursor="arrow")
                self.btn_dinamica.configure(cursor="hand2")
            
            win.protocol("WM_DELETE_WINDOW", ao_fechar_dinamica)
            win.on_voltar = ao_fechar_dinamica  # Permite o botão "Voltar" da própria janela

        except Exception as e:
            self.deiconify()
            self.configure(cursor="arrow")
            self.btn_dinamica.configure(cursor="hand2")
            tk.messagebox.showerror("Erro", f"Erro: {e}")

    # --- EXPORTA DADOS ---
    def exportar(self):  
        DialogoExportacao(self, self.df, self.janelas) # Exporta o DataFrame original

    # --- ADICIONAR À SÉRIE HISTÓRICA ---
    # --- ADICIONAR À SÉRIE HISTÓRICA (COM VERIFICAÇÃO DE DUPLICIDADE) ---
    def adicionar_serie_historica(self):
        nome_arquivo = "Serie_historica.xlsx"
        
        # 1. Identifica o que estamos tentando salvar (quais Hospitais, Meses e
        # Âmbitos tem na tabela atual). Inclui o hospital na chave: sem isso,
        # subir dados de um hospital novo no mesmo mês/âmbito de outro já
        # salvo apagaria por engano os dados do hospital antigo.
        try:
            novos_dados_resumo = self.df[
                ["Hospital/Prestador", "Mês/Ano", "Âmbito Serviço"]
            ].drop_duplicates().values.tolist()
        except Exception:
            novos_dados_resumo = []

        # Mensagem padrão
        msg_confirmacao = f"Deseja adicionar {len(self.df)} registros ao arquivo '{nome_arquivo}'?"
        substituir = False

        # 2. Verifica se o arquivo já existe e se tem conflito
        if os.path.exists(nome_arquivo):
            try:
                df_hist = pd.read_excel(nome_arquivo)
                
                # Verifica se as colunas necessárias existem para comparar
                colunas_chave = ["Hospital/Prestador", "Mês/Ano", "Âmbito Serviço"]
                if novos_dados_resumo and all(c in df_hist.columns for c in colunas_chave):
                    conflitos = []
                    for hospital, mes, ambito in novos_dados_resumo:
                        # Filtra o histórico para ver se já tem esse hospital+mês+âmbito
                        filtro = (
                            (df_hist["Hospital/Prestador"] == hospital)
                            & (df_hist["Mês/Ano"] == mes)
                            & (df_hist["Âmbito Serviço"] == ambito)
                        )
                        if not df_hist[filtro].empty:
                            conflitos.append(f"- {hospital} — {ambito} de {mes}")
                    
                    # Se achou conflito, muda a mensagem para AVISO
                    if conflitos:
                        lista_str = "\n".join(conflitos)
                        msg_confirmacao = (
                            f"⚠️ ATENÇÃO: Já existem dados salvos para:\n{lista_str}\n\n"
                            "Se você confirmar, os dados ANTIGOS desses períodos serão SUBSTITUÍDOS pelos novos.\n\n"
                            "Deseja SUBSTITUIR os dados antigos pelos novos?"
                        )
                        substituir = True
            except Exception as e:
                print(f"Erro ao ler histórico para verificação: {e}")

        # 3. Pede confirmação ao usuário
        if not messagebox.askyesno("Confirmar Histórico", msg_confirmacao, parent=self):
            return

        # 4. Executa a gravação
        try:
            df_final = self.df.copy()
            novo_arquivo = False

            if os.path.exists(nome_arquivo):
                # Lê o histórico original
                df_hist = pd.read_excel(nome_arquivo)
                
                if substituir and novos_dados_resumo:
                    # REMOVE os dados antigos que batem com os novos (Limpeza)
                    for hospital, mes, ambito in novos_dados_resumo:
                        mascara = ~(
                            (df_hist["Hospital/Prestador"] == hospital)
                            & (df_hist["Mês/Ano"] == mes)
                            & (df_hist["Âmbito Serviço"] == ambito)
                        )
                        df_hist = df_hist[mascara]
                
                # Junta o histórico (agora limpo) com os novos dados
                df_final = pd.concat([df_hist, df_final], ignore_index=True)
            else:
                novo_arquivo = True

            # Salva no disco
            df_final.to_excel(nome_arquivo, index=False)
            
            # Tenta formatar bonitinho (se a função existir)
            try: formatar_excel_como_tabela(nome_arquivo)
            except: pass

            acao = "criado" if novo_arquivo else ("atualizado (substituição)" if substituir else "atualizado (adição)")
            messagebox.showinfo("Sucesso", f"Histórico {acao} com sucesso!\n\nTotal de registros na série: {len(df_final)}", parent=self)

        except PermissionError:
            messagebox.showerror("Erro", f"O arquivo '{nome_arquivo}' está aberto no Excel.\nFeche-o e tente novamente.", parent=self)
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao salvar:\n{e}", parent=self)

# Extrator SIA/SIH
class ExtratorApp(IconedToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Extrator SIA/SIH")
        self.geometry("1100x600") # Aumentei a largura para caber o painel lateral
        
        # Centraliza a janela
        self.update_idletasks()
        try:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = (screen_width - 1100) // 2
            y = (screen_height - 650) // 2
            self.geometry(f"1100x600+{x}+{y}")
        except: pass
        
        self.files = []
        self.arquivo_historico = resource_path("recentes.json")
        
        # --- LAYOUT PRINCIPAL (GRID 2 COLUNAS) ---
        self.grid_columnconfigure(0, weight=1) # Coluna Esquerda (Principal)
        self.grid_columnconfigure(1, weight=0) # Coluna Direita (Lateral Fixa)
        self.grid_rowconfigure(0, weight=1)

        # === PAINEL ESQUERDO: LISTA ATUAL E DROP ===
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        
        ctk.CTkLabel(self.left_frame, text="Upload de Arquivos", font=("Segoe UI", 24, "bold"), text_color="#1A1A1A").pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(self.left_frame, text="Arraste arquivos PDF ou selecione manualmente", font=("Segoe UI", 12), text_color="#777777").pack(anchor="w", pady=(0, 20))

        # Drop Area (Estilo "Tracejado" simulado com borda cinza)
        self.drop_frame = ctk.CTkFrame(self.left_frame, border_width=2, border_color="#D5D5D5", fg_color="#F2F2F2", corner_radius=10)
        self.drop_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.lbl_drop = ctk.CTkLabel(self.drop_frame, text="Solte os arquivos aqui", font=("Segoe UI", 14), text_color="#888888")
        self.lbl_drop.place(relx=0.5, rely=0.5, anchor="center")

        self.list_frame = ctk.CTkScrollableFrame(self.drop_frame, fg_color="transparent")

        # Botões de Ação (Minimalistas)
        btn_box = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        btn_box.pack(pady=0, fill="x")

        ctk.CTkButton(btn_box, text="Selecionar Arquivos", width=160, height=35, fg_color="#E4E4E4", hover_color="#D6D6D6", text_color="#1A1A1A", command=self.add_manual).pack(side="left")
        ctk.CTkButton(btn_box, text="Limpar Tudo", width=120, height=35, fg_color="transparent", text_color="#C53030", hover_color="#FBE4E4", command=self.limpar).pack(side="right")
        
        # Botão Processar (CTA - Call to Action)
        self.btn_run = ctk.CTkButton(self.left_frame, text="INICIAR PROCESSAMENTO", height=50, font=("Segoe UI", 14, "bold"), fg_color="#007ACC", hover_color="#0063A5", corner_radius=8, command=self.run)
        self.btn_run.pack(fill="x", pady=(20, 0))
        
        # Barra de Progresso e Label de Status
        self.progress = ctk.CTkProgressBar(self.left_frame)
        self.progress.pack(fill="x", pady=(10, 5))
        self.progress.set(0)
        self.lbl = ctk.CTkLabel(self.left_frame, text="Aguardando...")
        self.lbl.pack()

        # === PAINEL DIREITO: HISTÓRICO/RECENTES ===
        self.right_frame = ctk.CTkFrame(self, width=500, corner_radius=0, fg_color="#EFEFEF")
        self.right_frame.grid(row=0, column=1, sticky="ns", padx=0, pady=0)
        self.right_frame.grid_propagate(True)
        # 1. CABEÇALHO (Fica no Topo)
        frm_head = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        frm_head.pack(side="top", fill="x", padx=20, pady=(30, 10))

        ctk.CTkLabel(frm_head, text="Recentes", font=("Segoe UI", 16, "bold"), text_color="#333333").pack(side="left")
        ctk.CTkButton(frm_head, text="Limpar", width=60, height=20, font=("Segoe UI", 11), fg_color="transparent", text_color="#777", hover_color="#E0E0E0", command=self.limpar_historico_recentes).pack(side="right")

        # 2. RODAPÉ DE BOTÕES (Fica Embaixo - Criamos primeiro para garantir o lugar dele)
        # Usamos side="bottom" para colar no chão da janela
        frm_footer = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        frm_footer.pack(side="bottom", fill="x", padx=20, pady=20)

    # --- BOTÃO ABRIR SÉRIE HISTÓRICA ---
        # Botão Série Histórica (Último item)
        ctk.CTkButton(
            frm_footer, 
            text="Abrir Série Histórica", 
            font=("Segoe UI", 12), 
            fg_color="transparent", border_width=1, border_color="#444", text_color="#AAA", hover_color="#222",
            height=40,
            command=self.abrir_serie_historica
        ).pack(side="bottom", fill="x") # Pack bottom dentro do footer

        ttk.Separator(frm_footer, orient='horizontal').pack(side="bottom", fill='x', pady=15)

        # Botão Reutilizar (Logo acima do separador)
        self.btn_add_recents = ctk.CTkButton(
            frm_footer, 
            text="Reutilizar Selecionados", 
            font=("Segoe UI", 12), 
            fg_color="#2D2D30", hover_color="#3E3E42", 
            command=self.adicionar_selecionados_recentes
        )
        self.btn_add_recents.pack(side="bottom", fill="x")

        # 3. LISTA DE ARQUIVOS (Ocupa o que sobrou no Meio)
        # Importante: expand=True faz ele comer todo o espaço vazio entre o Header e o Footer
        self.scroll_recents = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent", width=400) # Largura fixa
        self.scroll_recents.pack(side="top", fill="both", expand=True, padx=5, pady=5) # Preenche o espaço restante

        

        # Configura Drag and Drop
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.drop)
        except: print("Aviso: Drag and Drop falhou na inicialização.")

        # Inicializa lista de recentes
        self.vars_recentes = {} 
        self.selecionados_recentes = {}
        # --- NOVO: Variáveis para lógica de seleção avançada ---
        self.lista_botoes_recentes = []   # Guarda os objetos dos botões
        self.lista_caminhos_recentes = [] # Guarda os caminhos na mesma ordem
        self.ultimo_indice_clicado = None # Lembra qual foi o último para o SHIFT
       
       # --- CORREÇÃO OBRIGATÓRIA AQUI ---
        self.lista_widgets_arquivos = []  
        
        # ---------------------------------
        # --- NOVO: BINDINGS PARA O LADO ESQUERDO (DESMARCAR) ---
        # Faz com que clicar na área de upload ou no fundo esquerdo também limpe a seleção da direita
        self.left_frame.bind("<Button-1>", self.desmarcar_recentes)
        self.drop_frame.bind("<Button-1>", self.desmarcar_recentes)
        self.list_frame.bind("<Button-1>", self.desmarcar_recentes)
        try:
            # Tenta vincular o fundo interno da lista de upload também
            self.list_frame._parent_canvas.bind("<Button-1>", self.desmarcar_recentes)
        except: pass
        # -------------------------------------------------------

        self.carregar_painel_recentes()


    # --- LÓGICA DE RECENTES ---
    # --- LÓGICA DE RECENTES (Visual Clean) ---
    def carregar_painel_recentes(self):
        # Limpa o painel visual
        for w in self.scroll_recents.winfo_children(): w.destroy()
        
        # --- CORREÇÃO DE CLIQUE NO VAZIO ---
        # 1. Vincula na moldura externa
        self.scroll_recents.bind("<Button-1>", self.desmarcar_recentes)
        
        # 2. Vincula na tela de fundo interna (Canvas) - O SEGREDINHO
        # Isso captura o clique no espaço vazio entre ou abaixo dos itens
        try:
            self.scroll_recents._parent_canvas.bind("<Button-1>", self.desmarcar_recentes)
        except: pass
        
        # 3. Vincula no painel lateral geral
        self.right_frame.bind("<Button-1>", self.desmarcar_recentes)
        # -----------------------------------

        self.selecionados_recentes = {}
        self.lista_botoes_recentes = []
        self.lista_caminhos_recentes = []
        self.ultimo_indice_clicado = None
        
        historico = []
        if os.path.exists(self.arquivo_historico):
            try:
                with open(self.arquivo_historico, "r", encoding="utf-8") as f:
                    historico = json.load(f)
            except: pass
        
        if not historico:
            lbl = ctk.CTkLabel(self.scroll_recents, text="Nenhum histórico.", text_color="#555")
            lbl.pack(pady=20)
            # Permite clicar no label para desmarcar também
            lbl.bind("<Button-1>", self.desmarcar_recentes)
            return

        for path in historico:
            if not os.path.exists(path): continue
            
            nome_arquivo = os.path.basename(path)
            self.selecionados_recentes[path] = False
            
            btn = ctk.CTkButton(
                self.scroll_recents, 
                text=nome_arquivo, 
                font=("Segoe UI", 12), 
                fg_color="transparent",   
                text_color="#BBBBBB",     
                hover_color="#2A2A2A",    
                anchor="w",
                height=28
            )
            btn.pack(pady=1, padx=2, fill="x")
            
            indice_correto = len(self.lista_caminhos_recentes)
            
            # Clique Simples (Seleção)
            btn.bind("<Button-1>", lambda e, i=indice_correto: self.ao_clicar_recente(e, i))
            
            # Clique Duplo (Enviar para processamento)
            btn.bind("<Double-1>", lambda e, p=path: self.ao_duplo_clique_recente(e, p))
            
            self.lista_botoes_recentes.append(btn)
            self.lista_caminhos_recentes.append(path)
            
            CTkToolTip(btn, path)


    # Lógica de clique em arquivo recente (com SHIFT)
    def remover_arquivo(self, path): # Remove arquivo da lista atual
        if path in self.files:
            self.files.remove(path)
            self.update_list()
    
    # Adiciona os arquivos recentes selecionados à lista principal
    def adicionar_selecionados_recentes(self):
        adicionados = 0
        for path, selecionado in self.selecionados_recentes.items():
            if selecionado:
                if path not in self.files:
                    self.files.append(path)
                    adicionados += 1
                self.selecionados_recentes[path] = False  # Desmarca após usar
        
        if adicionados > 0:
            self.update_list()
            self.carregar_painel_recentes()  # Recarrega para resetar cores
        else:
            messagebox.showinfo("Info", "Selecione arquivos na lista à direita ou arquivos já adicionados.")

    # Salva o histórico de arquivos processados em JSON
    def salvar_historico(self):
        # Carrega histórico existente
        atual = []
        if os.path.exists(self.arquivo_historico):
            try:
                with open(self.arquivo_historico, "r", encoding="utf-8") as f:
                    atual = json.load(f)
            except: pass
            
        # Adiciona os arquivos atuais no topo (sem duplicar)
        novos = [f for f in self.files if f not in atual]
        lista_final = novos + atual
        
        # Limita a 30 itens para não ficar gigante
        lista_final = lista_final[:30]
        
        try:
            with open(self.arquivo_historico, "w", encoding="utf-8") as f:
                json.dump(lista_final, f, ensure_ascii=False)
        except: pass
        
        # Atualiza o painel visualmente
        self.after(500, self.carregar_painel_recentes)

    # Função para apagar todo o histórico de recentes
    def limpar_historico_recentes(self):
        # Pergunta de segurança
        if not messagebox.askyesno("Confirmar", "Deseja apagar todo o histórico de arquivos recentes?", parent=self):
            return

        # 1. Apaga o arquivo JSON
        if os.path.exists(self.arquivo_historico):
            try:
                os.remove(self.arquivo_historico)
            except Exception as e:
                print(f"Erro ao apagar histórico: {e}")

        # 2. Reseta as variáveis internas
        self.selecionados_recentes = {}
        self.lista_botoes_recentes = []
        self.lista_caminhos_recentes = []
        self.ultimo_indice_clicado = None

        # 3. Recarrega o painel (vai mostrar "Nenhum histórico")
        self.carregar_painel_recentes()

    # --- DESMARCAR AO CLICAR FORA ---
    def desmarcar_recentes(self, event=None):
        # Define todos como False
        for p in self.selecionados_recentes:
            self.selecionados_recentes[p] = False
        self.ultimo_indice_clicado = None
        
        # Atualiza visual e foca na janela para tirar foco de botões
        self.atualizar_cores_recentes()
        self.focus_set()

    # --- MÉTODOS PADRÃO (Drop, Run, etc) ---
    def drop(self, e):
        raw_files = re.findall(r'\{.*?\}|\S+', e.data)
        for f in raw_files:
            f = f.replace("{", "").replace("}", "")
            if f.lower().endswith(".pdf") and f not in self.files: self.files.append(f)
        self.update_list()

# --- MÉTODOS PADRÃO (Drop, Run, etc) ---
    def add_manual(self):
        fs = filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])
        for f in fs: self.files.append(f)
        self.update_list()

# --- ATUALIZA A LISTA DE ARQUIVOS ---
    # --- ATUALIZAÇÃO DO UPDATE_LIST (Sem ícones de arquivo) ---
    # NA CLASSE ExtratorApp
    # --- ATUALIZA A LISTA DE ARQUIVOS (CORRIGIDO) ---
    def update_list(self):
        if self.files:
            self.lbl_drop.place_forget()
            self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Limpa widgets anteriores
            for widget in self.lista_widgets_arquivos:
                try: widget.destroy()
                except: pass
            self.lista_widgets_arquivos = [] 

            for f in self.files:
                # Card Minimalista (Cinza escuro, cantos arredondados)
                frm = ctk.CTkFrame(self.list_frame, fg_color="#252526", corner_radius=4)
                frm.pack(fill="x", pady=2, padx=5)
                self.lista_widgets_arquivos.append(frm) 

                # Nome do arquivo
                nome = os.path.basename(f)
                if len(nome) > 70: nome = nome[:65] + "..."
                    
                lbl_nome = ctk.CTkLabel(frm, text=nome, anchor="w", font=("Segoe UI", 12), text_color="#E0E0E0")
                lbl_nome.pack(side="left", padx=10, pady=8, fill="x", expand=True)
                
                # CORREÇÃO: Botão X sem o parâmetro 'hover_text_color' que dava erro
                btn_del = ctk.CTkButton(
                    frm, 
                    text="✕", 
                    width=30, height=30, 
                    font=("Arial", 14),
                    fg_color="transparent", 
                    text_color="#AAAAAA",     # Cinza claro
                    hover_color="#C0392B",    # Fundo vermelho ao passar mouse
                    command=lambda path=f: self.remover_arquivo(path)
                )
                btn_del.pack(side="right", padx=0)
                
        else:
            self.list_frame.pack_forget()
            self.lbl_drop.place(relx=0.5, rely=0.5, anchor="center")

# --- LIMPA A LISTA DE ARQUIVOS ---
    def limpar(self): 
        self.files = []
        self.update_list()


    # --- NOVO MÉTODO RUN SEGURO ---
    def run(self):
        # 1. Validações iniciais
        if any(self.selecionados_recentes.values()):
            self.adicionar_selecionados_recentes()

        if not self.files:
            return messagebox.showwarning("!", "Adicione arquivos para processar.", parent=self)

        self.salvar_historico()
        self.btn_run.configure(state="disabled", text="PROCESSANDO...")

        # 2. Inicia a thread apontando para um método wrapper (envelope)
        t = threading.Thread(target=self._thread_wrapper, daemon=True)
        t.start()

    # --- ENVELOPE DA THREAD (A MÁGICA ACONTECE AQUI) ---
    def _thread_wrapper(self):
        try:
            # Executa o trabalho pesado na Thread Secundária (ISSO PODE)
            df_resultado = executar_extracao_completa(self.files, self.upd)

            # AGORA VEM A CORREÇÃO:
            # Agendamos a execução do 'self.end' na Thread Principal usando .after(0, ...)
            # O .after coloca a função na fila do mainloop do Tkinter
            self.after(0, lambda: self.end(df_resultado))

        except Exception as e:
            # Se der erro, também agendamos o aviso na Thread Principal
            self.after(0, lambda: self.tratamento_erro_thread(str(e)))

    # Método auxiliar para mostrar erro de forma segura
    def tratamento_erro_thread(self, msg_erro):
        self.btn_run.configure(state="normal", text="INICIAR PROCESSAMENTO")
        self.progress.set(0)
        self.lbl.configure(text="Erro.")
        messagebox.showerror("Erro Crítico", f"Falha no processamento:\n{msg_erro}", parent=self)

    # Método auxiliar para organizar o código da thread
    def _processar_thread(self):
        try:
            # Chama a extração passando a função segura 'upd'
            df = executar_extracao_completa(self.files, self.upd)
            # Agenda a finalização na thread principal (UI)
            self.after(0, lambda: self.end(df))
        except Exception as e:
            # Em caso de erro crítico no script de extração
            self.after(0, lambda: messagebox.showerror("Erro no Processamento", str(e), parent=self))
            self.after(0, lambda: self.end(pd.DataFrame())) # Finaliza com DF vazio para resetar botões



    # --- ATUALIZA A BARRA DE PROGRESSO (CORRIGIDO ANTI-CRASH) ---

    def _safe_upd(self, text, value):
        # Checagem dupla de segurança
        if self.winfo_exists():
            self.lbl.configure(text=text)
            self.progress.set(value)

    # --- ATUALIZA A BARRA DE PROGRESSO (THREAD-SAFE CORRIGIDO) ---
    def upd(self, texto, valor):
        # REMOVA O self.winfo_exists() DAQUI! Ele causa o erro na thread.
        # Apenas agendamos a execução segura na thread principal.
        try:
            self.after(0, lambda: self._realizar_update_visual(texto, valor))
        except:
            pass

    def _realizar_update_visual(self, texto, valor):
        # A checagem de existência deve ser feita AQUI, na thread principal
        if not self.winfo_exists(): return

        try:
            self.lbl.configure(text=texto)
            self.progress.set(valor)
        except:
            pass


    def _atualizar_ui_progresso(self, texto, valor):
        # Atualização efetiva (só roda na Main Thread)
        try:
            self.lbl.configure(text=texto)
            self.progress.set(valor)
        except:
            pass
# --- FINALIZA O PROCESSAMENTO ---
    # --- FINALIZA O PROCESSAMENTO (Janela Principal fica atrás) ---
    # --- FINALIZA O PROCESSAMENTO ---
    def end(self, df):
        # Se a janela já fechou, não faz nada
        if not self.winfo_exists(): return
        
        def _concluir(): # Função auxiliar para concluir
            # 1. Reseta a interface principal para novo uso
            self.btn_run.configure(state="normal", text="INICIAR PROCESSAMENTO")
            self.progress.set(1.0) # Completa a barra
            self.lbl.configure(text="Concluído!")

            if df is not None and not df.empty:
                # 2. Abre a janela de resultados (Dados Brutos)
                try:
                    win = VisualizadorCompleto(self, df)

                    # ESCONDE A JANELA MÃE (Modo Foco) - evita telas empilhadas
                    self.withdraw()

                    def ao_fechar_completo():
                        win.destroy()
                        self.deiconify()  # REAPARECE A MÃE
                        self.lift()
                        self.focus_force()

                    win.protocol("WM_DELETE_WINDOW", ao_fechar_completo)
                    win.on_voltar = ao_fechar_completo  # Permite o botão "Voltar" da própria janela

                    # Força a nova janela para frente
                    win.lift()
                    win.focus_force()

                    # Garante que ela fique no topo
                    win.after(200, lambda: win.lift())
                    win.after(200, lambda: win.focus_force())
                except Exception as e:
                    messagebox.showerror("Erro Visualizador", f"Erro ao abrir tabela: {e}", parent=self)
                    
            else:
                # Se a extração retornou vazio (mas sem crashar o script)
                messagebox.showwarning("Aviso", "Nenhum dado válido foi extraído dos arquivos.\nVerifique se são arquivos SIA/SIH válidos.", parent=self)
                self.progress.set(0)
                self.lbl.configure(text="Aguardando...")

         # Agenda para rodar imediatamente
        self.after(0, _concluir) # Função auxiliar para concluir

        
# --- LÓGICA DE SELEÇÃO AVANÇADA DE RECENTES ---
    def ao_clicar_recente(self, event, index_atual):
        # Verifica se as teclas estão pressionadas (bitmask do Tkinter)
        # 0x0004 é Control, 0x0001 é Shift
        ctrl_pressed = (event.state & 0x4) != 0
        shift_pressed = (event.state & 0x1) != 0
        
        path_atual = self.lista_caminhos_recentes[index_atual]

        if shift_pressed and self.ultimo_indice_clicado is not None:
            # --- LÓGICA DO SHIFT (Intervalo) ---
            start = min(self.ultimo_indice_clicado, index_atual)
            end = max(self.ultimo_indice_clicado, index_atual)
            
            # Seleciona tudo no intervalo (inclusive)
            for i in range(start, end + 1):
                p = self.lista_caminhos_recentes[i]
                self.selecionados_recentes[p] = True
                
        elif ctrl_pressed:
            # --- LÓGICA DO CTRL (Alternar individual) ---
            # Inverte o estado atual apenas deste item
            estado_atual = self.selecionados_recentes.get(path_atual, False)
            self.selecionados_recentes[path_atual] = not estado_atual
            self.ultimo_indice_clicado = index_atual
            
        else:
            # --- CLIQUE NORMAL (Seleção Exclusiva) ---
            # Desmarca todos
            for p in self.selecionados_recentes:
                self.selecionados_recentes[p] = False
            
            # Seleciona apenas o atual
            self.selecionados_recentes[path_atual] = True
            self.ultimo_indice_clicado = index_atual

        # Atualiza as cores visualmente
        self.atualizar_cores_recentes()
        return "break"  # Impede que o clique passe para o fundo (scroll_recents)

    # --- NOVO: AÇÃO DE CLIQUE DUPLO (Envia direto para a lista) ---
    def ao_duplo_clique_recente(self, event, path):
        # Verifica se o arquivo já está na lista para não duplicar
        if path not in self.files:
            self.files.append(path)
            self.update_list()
            
            # Feedback visual rápido (opcional: piscar a borda ou mudar cor momentaneamente)
            # Mas a atualização da lista à esquerda já serve como feedback visual.

# --- ATUALIZA AS CORES DOS BOTÕES DE RECENTES ---
    # --- ATUALIZA AS CORES DOS BOTÕES DE RECENTES (Estilo SaaS) ---
    # --- ATUALIZA AS CORES DOS BOTÕES DE RECENTES (COM FEEDBACK NO BOTÃO DE AÇÃO) ---
    def atualizar_cores_recentes(self):
        algum_selecionado = False
        contador = 0

        # 1. Atualiza visual da lista (itens individuais)
        for i, btn in enumerate(self.lista_botoes_recentes):
            path = self.lista_caminhos_recentes[i]
            selecionado = self.selecionados_recentes.get(path, False)
            
            if selecionado:
                algum_selecionado = True
                contador += 1
                # Item da lista selecionado (Azul)
                btn.configure(fg_color="#007ACC", hover_color="#014F8A", text_color="white") 
            else:
                # Item normal (Transparente)
                btn.configure(fg_color="transparent", text_color="#BBBBBB")

        # 2. Atualiza o Botão Grande ("Reutilizar Selecionados")
        if algum_selecionado:
            self.btn_add_recents.configure(
                state="normal",
                text=f"Reutilizar Selecionados ({contador})",  # Mostra quantos
                fg_color="#007ACC",       # AZUL ACESO (Primary)
                hover_color="#005A9E",
                text_color="white"
            )
        else:
            self.btn_add_recents.configure(
                state="disabled",         # Desabilita clique
                text="Reutilizar Selecionados",
                fg_color="#2D2D30",       # CINZA ESCURO (Apagado)
                hover_color="#2D2D30",    # Sem efeito hover
                text_color="#555555"
            )

    # --- ABRE A SÉRIE HISTÓRICA NO VISUALIZADOR ---
    def abrir_serie_historica(self):
        nome_arquivo = "Serie_historica.xlsx"
        
        if not os.path.exists(nome_arquivo):
            messagebox.showwarning("Não encontrado", f"O arquivo '{nome_arquivo}' ainda não existe.\n\nVocê precisa processar arquivos e clicar em '+ Série Histórica' na tela de resultados para criá-lo.", parent=self)
            return
            
        try:
            # Desabilita o botão momentaneamente para evitar clique duplo
            self.configure(cursor="watch")
            self.update()
            
            # Carrega o Excel
            df_hist = pd.read_excel(nome_arquivo)
            
            # Padroniza colunas de valores (caso o Excel tenha salvado como texto)
            if "Valor" in df_hist.columns:
                df_hist["Valor"] = pd.to_numeric(df_hist["Valor"], errors='coerce').fillna(0.0)
            
            self.configure(cursor="")

            # Abre o Visualizador Completo com os dados do histórico
            win = VisualizadorCompleto(self, df_hist)

            # ESCONDE A JANELA MÃE (Modo Foco) - evita telas empilhadas
            self.withdraw()

            def ao_fechar_completo():
                win.destroy()
                self.deiconify()  # REAPARECE A MÃE
                self.lift()
                self.focus_force()

            win.protocol("WM_DELETE_WINDOW", ao_fechar_completo)
            win.on_voltar = ao_fechar_completo  # Permite o botão "Voltar" da própria janela

        except Exception as e:
            self.configure(cursor="")
            messagebox.showerror("Erro", f"Erro ao abrir Série Histórica:\n{e}", parent=self)



# --- FUNÇÃO CORRIGIDA E BLINDADA PARA ABRIR A JANELA ---
# --- FUNÇÃO COM TRANSIÇÃO SUAVE (FADE IN) ---
def abrir_janela(parent):
    try:
        # 1. Cria a janela normalmente
        app = ExtratorApp(parent)
        
        # 2. IMEDIATAMENTE define a opacidade como 0 (Invisível)
        # Isso impede que o usuário veja a lista de recentes sendo "desenhada"
        app.attributes("-alpha", 0.0)
        
        # --- Configurações de Bloqueio (Blindagem) ---
        app.transient(parent) # Mantém sobre o menu
        app.grab_set()        # Bloqueia cliques no menu atrás
        
        # Protocolo de fechamento seguro
        def fechar_seguro():
            # Efeito reverso (Fade Out) ao fechar (Opcional, mas elegante)
            def fade_out(alpha=1.0):
                if alpha > 0.0:
                    alpha -= 0.1
                    app.attributes("-alpha", alpha)
                    app.after(10, lambda: fade_out(alpha))
                else:
                    parent.grab_release()
                    app.destroy()
                    parent.focus_force()
            
            fade_out()

        app.protocol("WM_DELETE_WINDOW", fechar_seguro)
        
        # Garante a posição
        app.lift()
        
        # --- ANIMAÇÃO DE ENTRADA (FADE IN) ---
        def iniciar_fade_in():
            def step_fade(alpha=0.0):
                if alpha < 1.0:
                    # Aumenta a opacidade em passos de 0.05 (5%)
                    alpha += 0.05
                    app.attributes("-alpha", alpha)
                    # Chama o próximo passo em 10ms
                    app.after(10, lambda: step_fade(alpha))
                else:
                    # Garante que fique 100% visível no final
                    app.attributes("-alpha", 1.0)
                    app.focus_force()
            
            step_fade()

        # 3. Aguarda 200ms antes de começar a mostrar a janela
        # Esse tempo é suficiente para o Python carregar a lista de recentes e ícones
        app.after(200, iniciar_fade_in)
        
    except Exception as e:
        tk.messagebox.showerror("Erro", f"Não foi possível abrir o módulo: {e}")

# --- INÍCIO DO APLICATIVO ---
if __name__ == "__main__":
    # Configuração para alta DPI (evita janelas borradas)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    root = AppRoot()
    root.withdraw()  # Oculta a raiz vazia

    # Cria a janela do aplicativo
    app = ExtratorApp(root)


    # Quando fechar o ExtratorApp, mata a raiz também
    def fechar_tudo():
        try:
            root.quit()
            root.destroy()
        except:
            pass
        os._exit(0)  # Encerramento forçado do processo (brutal, mas eficiente para scripts travados)


    app.protocol("WM_DELETE_WINDOW", fechar_tudo)

    root.mainloop()