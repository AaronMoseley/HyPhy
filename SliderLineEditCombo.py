from PySide6.QtWidgets import QHBoxLayout, QSlider, QLineEdit, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator

class SliderLineEditCombo(QHBoxLayout):
    def __init__(self, name:str, defaultVal:float=None, min_val=0.0, max_val=100.0, decimals=2, parent=None):
        super().__init__(parent)

        self.min_val = min_val
        self.max_val = max_val
        self.decimals = decimals
        self.scale = 10 ** decimals

        # Create slider (as integer-based)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(min_val * self.scale))
        self.slider.setMaximum(int(max_val * self.scale))

        # Create line edit with validator
        self.line_edit = QLineEdit()
        validator = QDoubleValidator(min_val, max_val, decimals)
        self.line_edit.setValidator(validator)

        # Initial sync
        self.slider.setValue(int(min_val * self.scale))
        self.line_edit.setText(f"{min_val:.{decimals}f}")

        # Add widgets
        self.addWidget(QLabel(name))
        self.addWidget(self.line_edit)
        self.addWidget(self.slider)

        # Connect signals
        self.slider.valueChanged.connect(self._update_line_edit)
        self.line_edit.editingFinished.connect(self._update_slider)

        if defaultVal is not None:
            self.slider.setValue(defaultVal * self.scale)

    def _update_line_edit(self, value):
        float_val = value / self.scale
        self.line_edit.setText(f"{float_val:.{self.decimals}f}")

    def _update_slider(self):
        text = self.line_edit.text()
        try:
            value = float(text)
            slider_val = int(value * self.scale)
            if self.slider.minimum() <= slider_val <= self.slider.maximum():
                self.slider.setValue(slider_val)
        except ValueError:
            pass  # Ignore invalid input

    def value(self) -> float:
        """Returns the current value as a float."""
        return float(self.line_edit.text())