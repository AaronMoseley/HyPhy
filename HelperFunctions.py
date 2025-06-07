from PySide6.QtGui import QPixmap, QPen, QPainter, QColor, QImage
from PySide6.QtCore import QPoint

import re
import random
import numpy as np
import cv2

skeletonKey = "skeleton"
originalImageKey = "originalImage"
vectorKey = "vectorized"
linesKey = "lines"
pointsKey = "points"
clusterKey = "clusters"
functionKey = "function"

functionTypeKey = "type"
imageTypeKey = "image"
clusterTypeKey = "cluster"
lineTypeKey = "line"

def randomNumPerImage(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> float:
    return random.uniform(0, 1)

def randomNumPerCluster(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> list[float]:
    result = []
    
    for _ in range(len(clusters)):
        result.append(random.uniform(0, 1))

    return result

def randomNumPerLine(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> list[float]:
    result = []
    
    for _ in range(len(lines)):
        result.append(random.uniform(0, 1))

    return result

statFunctionMap = {
    "testCalc1": {
        functionKey: randomNumPerImage,
        functionTypeKey: imageTypeKey
    },
    "testCalc2": {
        functionKey: randomNumPerCluster,
        functionTypeKey: clusterTypeKey
    },
    "testCalc3": {
        functionKey: randomNumPerLine,
        functionTypeKey: lineTypeKey
    }
}

def camel_case_to_capitalized(text):
    """
    Converts a camel case string to a capitalized string with spaces.

    Args:
        text: The camel case string to convert.

    Returns:
        The capitalized string with spaces.
    """
    return re.sub(r"([A-Z])", r" \1", text).title()

def draw_lines_on_pixmap(points:list[tuple[float, float]], lines:list[list[int]], 
                         dimension:int=249, colorMap:dict={}, line_color=QColor("white"), line_width=2):
    pixmap = QPixmap(dimension, dimension)
    pixmap.fill(QColor("black"))

    painter = QPainter(pixmap)
    pen = QPen(line_color)
    pen.setWidth(line_width)
    painter.setPen(pen)

    # Helper to scale normalized points to pixel coordinates
    def scale_point(p):
        x = int(p[0] * dimension)
        y = int((1 - p[1]) * dimension)
        return QPoint(x, y)

    for lineIndex, line in enumerate(lines):
        if lineIndex in colorMap:
            pen.setColor(colorMap[lineIndex])
            painter.setPen(pen)
        else:
            pen.setColor(line_color)
            painter.setPen(pen)

        if len(line) < 2:
            continue
        for i in range(len(line) - 1):
            p1 = scale_point(points[line[i]])
            p2 = scale_point(points[line[i + 1]])
            painter.drawLine(p1, p2)

    painter.end()
    return pixmap

def ArrayToPixmap(array:np.ndarray, dimension:int=249, correctRange:bool=False) -> QPixmap:
    arrayCopy = np.copy(array)
    
    if not correctRange:
        arrayCopy *= 255.0

    arrayCopy = np.asarray(arrayCopy, dtype=np.uint8)

    # Resize using OpenCV
    resized_gray = cv2.resize(arrayCopy, (dimension, dimension), interpolation=cv2.INTER_CUBIC)

    # Convert to RGB by stacking channels
    rgb_array = cv2.cvtColor(resized_gray, cv2.COLOR_GRAY2RGB)

    height, width, channels = rgb_array.shape
    bytesPerLine = width * channels
    qImage = QImage(rgb_array.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
    qImage = qImage.copy()
    newPixmap = QPixmap.fromImage(qImage)
    return newPixmap

def NormalizeImageArray(array:np.ndarray) -> np.ndarray:
    arrayCopy = np.copy(array)
    
    maxValue = np.max(arrayCopy)
    minValue = np.min(arrayCopy)
    arrayCopy -= minValue
    maxValue -= minValue
    arrayCopy /= maxValue

    if arrayCopy.ndim > 2:
        return arrayCopy.mean(axis=-1)

    return arrayCopy

def DistanceToLine(P, A, B):
    P = np.array(P, dtype=float)
    A = np.array(A, dtype=float)
    B = np.array(B, dtype=float)
    
    AB = B - A
    AP = P - A
    AB_len_squared = np.dot(AB, AB)

    if AB_len_squared == 0:
        # A and B are the same point
        return np.linalg.norm(P - A)

    # Project point P onto the line AB, computing parameter t of the projection
    t = np.dot(AP, AB) / AB_len_squared

    if t < 0.0:
        # Closest to point A
        closest_point = A
    elif t > 1.0:
        # Closest to point B
        closest_point = B
    else:
        # Projection falls on the segment
        closest_point = A + t * AB

    # Return distance from P to the closest point
    return np.linalg.norm(P - closest_point)