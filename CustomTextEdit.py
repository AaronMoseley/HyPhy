from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Signal

class CustomTextEdit(QTextEdit):
    EditingFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.EditingFinished.emit()