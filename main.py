"""Ponto de entrada do Extrator SIA/SIH (interface em PySide6/Qt)."""
try:
    # No Windows, sem isso a barra de tarefas agrupa o processo como
    # "python.exe" genérico e mostra o ícone do interpretador em vez do
    # ícone da janela. Isso dá ao processo uma identidade própria.
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ExtratorSIASIH.App")
except Exception:
    pass

from ui_qt.app import main

if __name__ == "__main__":
    main()
