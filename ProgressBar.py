from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel
)
from PySide6.QtCore import Qt


class ProgressBarPopup(QWidget):
    def __init__(self, title="Progress", message="Processing...", maximum=100):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(200, 100)

        self.myLayout = QVBoxLayout()
        self.label = QLabel(message)
        self.progress_bar = QProgressBar()

        self.myLayout.addWidget(self.label)
        self.myLayout.addWidget(self.progress_bar)
        self.setLayout(self.myLayout)

        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(0)

    def set_maximum(self, maximum: int):
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(0)

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)
        if value >= self.progress_bar.maximum():
            self.close_popup()

    def increment(self, step: int = 1):
        current = self.progress_bar.value()
        new_value = current + step
        self.update_progress(new_value)

    def close_popup(self):
        self.close()