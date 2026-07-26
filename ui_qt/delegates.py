"""Delegates de item reutilizáveis entre as telas de tabela/árvore."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QStyledItemDelegate, QStyle

from ui_qt import theme


class SelecaoForteDelegate(QStyledItemDelegate):
    """Força fundo com a cor de destaque do tema atual + texto branco quando
    a célula está selecionada.

    Necessário porque: (1) em qualquer tema, a seleção deve ficar num "azul
    royal" forte e sempre legível, e (2) quando a célula já tem uma cor de
    fundo/texto própria (ex.: sombreamento por profundidade da Tabela
    Dinâmica), essa cor própria pode competir com `selection-color` do QSS e
    deixar o texto selecionado ilegível ou preso à cor normal do tema.
    """

    def paint(self, painter, option, index):
        if option.state & QStyle.State_Selected:
            painter.save()
            painter.fillRect(option.rect, QColor(theme.ACCENT))
            painter.setPen(QColor("#FFFFFF"))
            alinhamento = index.data(Qt.TextAlignmentRole)
            if not alinhamento:
                alinhamento = int(Qt.AlignLeft | Qt.AlignVCenter)
            rect = option.rect.adjusted(6, 0, -6, 0)
            painter.drawText(rect, alinhamento, str(index.data(Qt.DisplayRole) or ""))
            painter.restore()
        else:
            super().paint(painter, option, index)
