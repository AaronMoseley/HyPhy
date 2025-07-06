from PySide6.QtGui import QPixmap, QPen, QPainter, QColor, QImage
from PySide6.QtCore import QPoint

import re
import random
import numpy as np
import cv2
from scipy.stats import linregress
import math

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

timestampKey = "timestamp"
sampleKey = "sample"

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

#fractal dimension
def fractalDimension(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> float:
    # Ensure the array is binary
    array = np.array(skeleton, dtype=bool)

    # Get the array dimensions
    min_dim = min(array.shape)

    # Box sizes (powers of 2)
    box_sizes = 2 ** np.arange(int(np.log2(min_dim)))

    box_counts = []
    for box_size in box_sizes:
        # Count the number of boxes that contain at least one "1"
        box_count = 0
        for i in range(0, array.shape[0] - box_size + 1, box_size):
            for j in range(0, array.shape[1] - box_size + 1, box_size):
                if np.any(array[i:i+box_size, j:j+box_size]):
                    box_count += 1
        box_counts.append(box_count)

    # Convert to numpy arrays
    box_sizes = np.array(box_sizes)
    box_counts = np.array(box_counts)

    # Use linear regression to fit a line to log(box_counts) vs log(1/box_size)
    slope, _, _, _, _ = linregress(np.log(1/box_sizes), np.log(box_counts))

    # The slope of the line is the fractal dimension
    return slope

#number of lines in image
def numLinesInImage(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> int:
    return len(lines)

#number of clumps in image
def numClumpsInImage(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> int:
    return len(clusters)

#number of lines in each clump
def numLinesInClump(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> list[int]:
    result = [len(cluster) for cluster in clusters]
    return result

#average length of lines in clump
def averageLengthOfLinesInClump(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> list[float]:
    result = []

    for currentLines in clusters:
        totalLength = 0.0

        for lineIndex in currentLines:
            currentLine = lines[lineIndex]

            for i in range(len(currentLine) - 1):
                point1 = points[currentLine[i]]
                point2 = points[currentLine[i + 1]]

                segmentLength = math.sqrt(pow(point2[0] - point1[0], 2) + pow(point2[1] - point1[1], 2))

                totalLength += segmentLength

        averageLength = totalLength / len(currentLines)

        result.append(averageLength)

    return result

#whether each line is straight
def isLineStraight(skeleton:np.ndarray, lines:list[list[int]], points:list[tuple[float, float]], clusters:list[list[int]]) -> list[bool]:
    requirementForStraight = 0.95
    
    result = []

    for line in lines:
        numPointsInLine = len(line)
        
        if numPointsInLine <= 2:
            result.append(True)
            continue

        startPoint = points[line[0]]
        endPoint = points[line[-1]]
        midPoint = points[line[numPointsInLine // 2]]

        startToEnd = (endPoint[0] - startPoint[0], endPoint[1] - startPoint[1])
        startToEndLength = math.sqrt(pow(startToEnd[0], 2) + pow(startToEnd[1], 2))

        if startToEndLength < 0.01:
            result.append(True)
            continue

        startToEnd = (startToEnd[0] / startToEndLength, startToEnd[1] / startToEndLength)

        startToMid = (midPoint[0] - startPoint[0], midPoint[1] - startPoint[1])
        startToMidLength = math.sqrt(pow(startToMid[0], 2) + pow(startToMid[1], 2))

        if startToMidLength < 0.01:
            result.append(True)
            continue

        startToMid = (startToMid[0] / startToMidLength, startToMid[1] / startToMidLength)

        similarity = abs((startToEnd[0] * startToMid[0]) + (startToEnd[1] * startToMid[1]))

        if similarity > requirementForStraight:
            result.append(True)
        else:
            result.append(False)

    return result

statFunctionMap = {
    "fractalDimension": {
        functionKey: fractalDimension,
        functionTypeKey: imageTypeKey
    },
    "linesInImage": {
        functionKey: numLinesInImage,
        functionTypeKey: imageTypeKey
    },
    "clustersInImage": {
        functionKey: numClumpsInImage,
        functionTypeKey: imageTypeKey
    },
    "linesInCluster": {
        functionKey: numLinesInClump,
        functionTypeKey: clusterTypeKey
    },
    "averageLineLength": {
        functionKey: averageLengthOfLinesInClump,
        functionTypeKey: clusterTypeKey
    },
    "isLineStraight": {
        functionKey: isLineStraight,
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
                         dimension:int=249, colorMap:dict={}, line_color=QColor("white"), line_width=2, pixmap:QPixmap=None):
    if pixmap is None:
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

def ArrayToPixmap(array:np.ndarray, dimension:int=249, correctRange:bool=False, maxPoolDownSample:bool=False) -> QPixmap:
    arrayCopy = np.copy(array)
    
    if not correctRange:
        arrayCopy *= 255.0

    arrayCopy = np.asarray(arrayCopy, dtype=np.uint8)

    # Resize using OpenCV
    if not maxPoolDownSample:
        resized_gray = cv2.resize(arrayCopy, (dimension, dimension), interpolation=cv2.INTER_CUBIC)
    else:
        resized_gray = max_pooling_downsample(arrayCopy, (dimension, dimension))

    # Convert to RGB by stacking channels
    rgb_array = cv2.cvtColor(resized_gray, cv2.COLOR_GRAY2RGB)

    height, width, channels = rgb_array.shape
    bytesPerLine = width * channels
    qImage = QImage(rgb_array.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
    qImage = qImage.copy()
    newPixmap = QPixmap.fromImage(qImage)
    return newPixmap

def max_pooling_downsample(image: np.ndarray, output_shape: tuple) -> np.ndarray:
    """
    Downsamples a 2D grayscale image using max pooling, even when input
    dimensions are not divisible by the output dimensions.

    Parameters:
    - image (np.ndarray): 2D array of dtype np.uint8, shape (H, W)
    - output_shape (tuple): Target shape (new_H, new_W)

    Returns:
    - np.ndarray: Downsampled 2D array of shape output_shape, dtype np.uint8
    """
    input_h, input_w = image.shape
    output_h, output_w = output_shape

    pooled = np.zeros((output_h, output_w), dtype=np.uint8)

    for i in range(output_h):
        # Compute start and end row indices for pooling window
        start_i = int(i * input_h / output_h)
        end_i = int((i + 1) * input_h / output_h)

        for j in range(output_w):
            # Compute start and end column indices for pooling window
            start_j = int(j * input_w / output_w)
            end_j = int((j + 1) * input_w / output_w)

            # Extract pooling window and apply max
            window = image[start_i:end_i, start_j:end_j]
            pooled[i, j] = np.max(window)

    return pooled

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