from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap

import numpy as np

from HelperFunctions import draw_lines_on_pixmap, DistanceToLine

class InteractiveSkeletonPixmap(QLabel):
    clicked = Signal(float, float)

    def __init__(self, dimension:int=512, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)

        self.dimension = dimension

        self.points = None
        self.lines = None

    def SetLines(self, points:list[tuple[float, float]], lines:list[list[int]]) -> None:
        self.points = points
        self.lines = lines
        
        pixmap = draw_lines_on_pixmap(points, lines, self.dimension)
        self.setPixmap(pixmap)

    def mouseMoveEvent(self, event:QMouseEvent):
        x = event.x() / self.dimension
        y = 1 - (event.y() / self.dimension)

        if self.points is None or self.lines is None:
            return
        
        closestLine = -1
        closestDist = float("inf")

        for i in range(len(self.lines)):
            for j in range(len(self.lines[i]) - 1):
                startPoint = self.points[self.lines[i][j]]
                endPoint = self.points[self.lines[i][j + 1]]

                dist = DistanceToLine((x, y), startPoint, endPoint)

                if dist < closestDist:
                    closestDist = dist
                    closestLine = i

        print(closestLine)