from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

class ClickableLabel(QLabel):
    clicked = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event:QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event.x(), event.y())

        super().mousePressEvent(event)