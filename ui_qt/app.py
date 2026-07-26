"""Ponto de entrada do app Qt: monta a janela principal e liga as páginas."""
import sys

from PySide6.QtWidgets import QApplication

from ui_qt.main_window import MainWindow
from ui_qt.upload_page import UploadPage
from ui_qt.data_page import DataPage
from ui_qt.pivot_page import PivotPage


class Aplicacao:
    def __init__(self):
        self.qapp = QApplication.instance() or QApplication(sys.argv)
        self.window = MainWindow()  # aplica o tema salvo (ou o padrão) na criação

        self.upload_page = UploadPage(
            on_processed=self._abrir_dados_brutos,
            on_open_historico=self._abrir_dados_brutos,
        )
        self.window.set_home(self.upload_page, "Upload de Arquivos")

    def _abrir_dados_brutos(self, df):
        self.window.reset_to_home()
        data_page = DataPage(df, on_open_pivot=self._abrir_pivot)
        self.window.push_page(data_page, "Dados Brutos")

    def _abrir_pivot(self, df, data_page):
        # Sempre cria uma página nova: reaproveitar a antiga entre voltas de
        # navegação exigiria rastrear se o widget anterior já foi destruído
        # pelo Qt (MainWindow.voltar() faz deleteLater()), o que é frágil.
        # Dentro da própria Tabela Dinâmica dá para abrir várias abas ("+ Nova
        # Análise") sobre o mesmo conjunto de dados.
        pivot_page = PivotPage()
        data_page.pivot_page = pivot_page
        data_page.pivot_tabs_abertas = pivot_page.tabs
        pivot_page.nova_aba(df)
        self.window.push_page(pivot_page, "Tabela Dinâmica")

    def run(self):
        self.window.showMaximized()
        return self.qapp.exec()


def main():
    app = Aplicacao()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
