from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Signal
from PySide6.QtGui import QMouseEvent, QColor

import numpy as np
import math

from collections import deque

from HelperFunctions import draw_lines_on_pixmap, DistanceToLine

class InteractiveSkeletonPixmap(QLabel):
    clicked = Signal(float, float)
    PolylineHighlighted = Signal(float, float)

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

    def SetLines(self, points:list[tuple[float, float]], lines:list[list[int]]) -> None:
        self.points = points
        self.lines = lines
        self.GetClumps()

        pixmap = draw_lines_on_pixmap(points, lines, self.dimension)
        self.setPixmap(pixmap)

    def GetClumps(self) -> None:
        # Step 1: Build point-to-polyline index
        point_to_polylines = {}
        for i, polyline in enumerate(self.lines):
            for point in polyline:
                if point not in point_to_polylines:
                    point_to_polylines[point] = set()

                point_to_polylines[point].add(i)

        # Build connectivity graph between polylines
        graph = {}
        for i, polyline in enumerate(self.lines):
            if i not in graph:
                graph[i] = set()

            for point in polyline:
                for neighbor in point_to_polylines[point]:
                    if neighbor != i:
                        graph[i].add(neighbor)

        # Step 3: Find connected components using BFS or DFS
        visited = set()
        clusters = []

        for i in range(len(self.lines)):
            if i not in visited:
                queue = deque([i])
                cluster_indices = []
                while queue:
                    idx = queue.popleft()
                    if idx not in visited:
                        visited.add(idx)
                        cluster_indices.append(idx)
                        queue.extend(graph[idx] - visited)
                # Create flat list of polylines for the cluster
                clusters.append(cluster_indices)

        self.clumps = clusters

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

    def EmitLineLengths(self) -> None:
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

        self.PolylineHighlighted.emit(selectedLineLength, selectedClumpLength)

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
                self.EmitLineLengths()
        else:
            if self.selectedLineIndex is not None:
                self.selectedLineIndex = None
                self.selectedClumpIndex = None

                pixmap = draw_lines_on_pixmap(self.points, self.lines, self.dimension)
                self.setPixmap(pixmap)

                self.PolylineHighlighted.emit(-1, -1)