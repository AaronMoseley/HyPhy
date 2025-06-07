from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal
from PySide6.QtGui import QMouseEvent, QColor

import numpy as np
import math

from collections import deque

from HelperFunctions import draw_lines_on_pixmap, DistanceToLine

class InteractiveSkeletonPixmap(QLabel):
    #line length, clump length, line index, clump index
    PolylineHighlighted = Signal(float, float, int, int)

    def __init__(self, dimension:int=512, parent=None):
        super().__init__(parent)

        self.setMouseTracking(True)

        self.dimension = dimension

        self.points = None
        self.lines = None
        self.clumps = None

        self.selectedLineIndex = -1
        self.selectedClumpIndex = -1

        self.maxSelectDistance = 0.01

        self.selectedLineColor = QColor("purple")
        self.selectedClumpColor = QColor("red")

    def SetLines(self, points:list[tuple[float, float]], lines:list[list[int]], clumps:list[list[int]]) -> None:
        self.points = points
        self.lines = lines
        self.clumps = clumps

        pixmap = draw_lines_on_pixmap(points, lines, self.dimension)
        self.setPixmap(pixmap)

    def LineToClump(self, line:int) -> int:
        for i in range(len(self.clumps)):
            if line in self.clumps[i]:
                return i
            
        return -1
    
    def GetColorMap(self) -> dict:
        if self.selectedClumpIndex is None or self.selectedLineIndex is None:
            return {}
        
        result = {}

        for lineIndex in self.clumps[self.selectedClumpIndex]:
            result[lineIndex] = self.selectedClumpColor

        result[self.selectedLineIndex] = self.selectedLineColor

        return result
    
    def PointDistance(self, point1:tuple[float, float], point2:tuple[float, float]) -> float:
        return math.sqrt(pow(point2[0] - point1[0], 2) + pow(point2[1] - point1[1], 2))

    def EmitLineData(self) -> None:
        if self.selectedClumpIndex is None or self.selectedLineIndex is None:
            return
        
        selectedLineLength = 0.0
        for i in range(len(self.lines[self.selectedLineIndex]) - 1):
            selectedLineLength += self.PointDistance(self.points[self.lines[self.selectedLineIndex][i]], self.points[self.lines[self.selectedLineIndex][i + 1]])

        selectedClumpLength = 0.0
        for i in range(len(self.clumps[self.selectedClumpIndex])):
            lineIndex = self.clumps[self.selectedClumpIndex][i]

            for j in range(len(self.lines[lineIndex]) - 1):
                selectedClumpLength += self.PointDistance(self.points[self.lines[lineIndex][j]], self.points[self.lines[lineIndex][j + 1]])

        self.PolylineHighlighted.emit(selectedLineLength, selectedClumpLength, self.selectedLineIndex, self.selectedClumpIndex)

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

        if closestDist < self.maxSelectDistance:
            if closestLine != self.selectedLineIndex:
                self.selectedLineIndex = closestLine
                self.selectedClumpIndex = self.LineToClump(closestLine)

                colorMap = self.GetColorMap()
                pixmap = draw_lines_on_pixmap(self.points, self.lines, self.dimension, colorMap)
                self.setPixmap(pixmap)
                self.EmitLineData()
        else:
            if self.selectedLineIndex is not None:
                self.selectedLineIndex = None
                self.selectedClumpIndex = None

                pixmap = draw_lines_on_pixmap(self.points, self.lines, self.dimension)
                self.setPixmap(pixmap)

                self.PolylineHighlighted.emit(-1, -1, -1, -1)