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

def random_number_generator(skeleton:np.ndarray):
    return random.uniform(0, 1)

statFunctionMap = {
    "testCalc1": random_number_generator,
    "testCalc2": random_number_generator
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

def draw_lines_on_pixmap(points:list[tuple[float, float]], lines:list[list[int]], dimension:int=249, line_color=QColor("white"), line_width=2):
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

    for line in lines:
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