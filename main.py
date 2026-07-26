"""Ponto de entrada do Extrator SIA/SIH (interface em PySide6/Qt)."""
try:
    # No Windows, sem isso a barra de tarefas agrupa o processo como
    # "python.exe" genérico e mostra o ícone do interpretador em vez do
    # ícone da janela. Isso dá ao processo uma identidade própria.
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ExtratorSIASIH.App")
except Exception:
    pass

import logging

from ui_qt.main_window import dados_path

logging.basicConfig(
    filename=dados_path("erro_log.txt"),
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

from ui_qt.app import main

if __name__ == "__main__":
    main()
