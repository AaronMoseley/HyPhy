from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap

from HelperFunctions import draw_lines_on_pixmap

class InteractiveSkeletonPixmap(QLabel):
    clicked = Signal(float, float)

    def __init__(self, dimension:int=512, parent=None):
        super().__init__(parent)

        self.dimension = dimension

    def SetLines(self, points:list[tuple[float, float]], lines:list[list[int]]) -> None:
        pixmap = draw_lines_on_pixmap(points, lines, self.dimension)
        self.setPixmap(pixmap)