"""Execução em thread separada da extração dos PDFs (não trava a UI)."""
import pandas as pd
from PySide6.QtCore import QObject, QThread, Signal

from prod_SIA_SIH2xlsx import executar_extracao_completa


class ExtractionWorker(QObject):
    progress = Signal(str, float)
    finished = Signal(object)  # pd.DataFrame ou None em caso de erro fatal
    failed = Signal(str)

    def __init__(self, arquivos):
        super().__init__()
        self.arquivos = arquivos

    def run(self):
        try:
            df = executar_extracao_completa(self.arquivos, self._callback)
            self.finished.emit(df if df is not None else pd.DataFrame())
        except Exception as e:
            self.failed.emit(str(e))

    def _callback(self, texto, valor):
        self.progress.emit(texto, float(valor))


def iniciar_extracao(arquivos):
    """Cria a thread + worker prontos para uso.

    O chamador deve conectar os sinais `progress`/`finished`/`failed` do worker
    a métodos vinculados de um QObject (ex.: métodos de si mesmo) ANTES de
    chamar thread.start() — isso garante que o Qt despache as chamadas de
    volta para a thread principal automaticamente (conexão em fila), em vez
    de executá-las na própria thread de trabalho.
    """
    thread = QThread()
    worker = ExtractionWorker(arquivos)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(thread.deleteLater)

    return thread, worker
