from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal, QRect, Qt
from PySide6.QtGui import QMouseEvent, QColor

import numpy as np
import math

from collections import deque

from HelperFunctions import draw_lines_on_pixmap, DistanceToLine

class InteractiveSkeletonPixmap(QLabel):
    #line length, cluster length, line index, cluster index
    PolylineHighlighted = Signal(float, float, int, int)

    def __init__(self, dimension:int=512, parent=None):
        super().__init__(parent)

        if self.size().width() > dimension:
            dimension = self.size().width()

        self.setMouseTracking(True)

        self.dimension = dimension

        self.points = None
        self.lines = None
        self.clusters = None

        self.hoveredLineIndex = None
        self.hoveredClumpIndex = None

        self.selectedLineIndex = None
        self.selectedClumpIndex = None

        self.maxSelectDistance = 0.01

        self.selectedLineColor = QColor("purple")
        self.selectedClumpColor = QColor("red")

        self.hoveredLineColor = QColor("yellow")

    def SetLines(self, points:list[tuple[float, float]], lines:list[list[int]], clusters:list[list[int]]) -> None:
        self.points = points
        self.lines = lines
        self.clusters = clusters

        self.UpdateLines()

    def LineToClump(self, line:int) -> int:
        for i in range(len(self.clusters)):
            if line in self.clusters[i]:
                return i
            
        return -1
    
    def GetColorMap(self) -> dict:
        if self.hoveredClumpIndex is None and self.hoveredLineIndex is None \
            and self.selectedLineIndex is None and self.selectedClumpIndex is None:
            return {}
        
        result = {}

        if self.selectedClumpIndex is not None:
            for lineIndex in self.clusters[self.selectedClumpIndex]:
                result[lineIndex] = self.selectedClumpColor

        if self.hoveredLineIndex is not None:
            result[self.hoveredLineIndex] = self.hoveredLineColor

        if self.selectedLineIndex is not None:
            result[self.selectedLineIndex] = self.selectedLineColor

        return result
    
    def PointDistance(self, point1:tuple[float, float], point2:tuple[float, float]) -> float:
        return math.sqrt(pow(point2[0] - point1[0], 2) + pow(point2[1] - point1[1], 2))

    def EmitLineData(self) -> None:
        if self.hoveredClumpIndex is None or self.hoveredLineIndex is None:
            return
        
        selectedLineLength = 0.0
        for i in range(len(self.lines[self.hoveredLineIndex]) - 1):
            selectedLineLength += self.PointDistance(self.points[self.lines[self.hoveredLineIndex][i]], self.points[self.lines[self.hoveredLineIndex][i + 1]])

        selectedClumpLength = 0.0
        for i in range(len(self.clusters[self.hoveredClumpIndex])):
            lineIndex = self.clusters[self.hoveredClumpIndex][i]

            for j in range(len(self.lines[lineIndex]) - 1):
                selectedClumpLength += self.PointDistance(self.points[self.lines[lineIndex][j]], self.points[self.lines[lineIndex][j + 1]])

        self.PolylineHighlighted.emit(selectedLineLength, selectedClumpLength, self.hoveredLineIndex, self.hoveredClumpIndex)

    def mouseMoveEvent(self, event:QMouseEvent):
        #x = event.x() / self.dimension
        #y = 1 - ((event.y() - self.pos().y()) / self.dimension)
        #y += 0.5
        #y = event.y() / self.dimension

        #print(f"{x} {y}")

        #print(y)

        pos = event.pos()  # QPoint relative to the label
        pixmap = self.pixmap()

        if pixmap is None:
            return
        
        if self.points is None or self.lines is None:
            return
        
        label_size = self.size()
        pixmap_size = pixmap.size()

        # Default: assume pixmap is drawn at original size
        drawn_width = pixmap_size.width()
        drawn_height = pixmap_size.height()

        if drawn_width > label_size.width() or drawn_height > label_size.height():
            # Pixmap needs to be scaled down to fit label
            pixmap_ratio = pixmap_size.width() / pixmap_size.height()
            label_ratio = label_size.width() / label_size.height()

            if pixmap_ratio > label_ratio:
                # Width-constrained
                drawn_width = label_size.width()
                drawn_height = int(drawn_width / pixmap_ratio)
            else:
                # Height-constrained
                drawn_height = label_size.height()
                drawn_width = int(drawn_height * pixmap_ratio)

        # Center the pixmap inside the label
        x_offset = (label_size.width() - drawn_width) // 2
        y_offset = (label_size.height() - drawn_height) // 2

        # Create the actual drawn pixmap rectangle
        pixmap_rect = QRect(x_offset, y_offset, drawn_width, drawn_height)

        if pixmap_rect.contains(pos):
            local_x = pos.x() - x_offset
            local_y = pos.y() - y_offset

            x = local_x / drawn_width
            y = local_y / drawn_height
        else:
            return

        y = 1 - y

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

        if closestDist < self.maxSelectDistance:
            if closestLine != self.hoveredLineIndex:
                self.hoveredLineIndex = closestLine
                self.hoveredClumpIndex = self.LineToClump(closestLine)

                self.UpdateLines()
                self.EmitLineData()
        else:
            if self.hoveredLineIndex is not None:
                self.hoveredLineIndex = None
                self.hoveredClumpIndex = None

                self.UpdateLines()

                self.PolylineHighlighted.emit(-1, -1, -1, -1)

    def mousePressEvent(self, event:QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.hoveredLineIndex is not None:
                self.selectedLineIndex = self.hoveredLineIndex
                self.selectedClumpIndex = self.hoveredClumpIndex
            else:
                self.selectedLineIndex = None
                self.selectedClumpIndex = None

            self.UpdateLines()

    def UpdateLines(self) -> None:
        colorMap = self.GetColorMap()
        pixmap = draw_lines_on_pixmap(self.points, self.lines, self.dimension, colorMap)
        self.setPixmap(pixmap)