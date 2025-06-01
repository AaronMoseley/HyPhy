import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import math

def GetInitialLines(skeleton:np.ndarray) -> tuple[list, list]:
    #create stack
    stack = []

    #create line assignment array, assign each point to a line or junction
    lineAssignments = np.zeros_like(skeleton)

    #create point assignment array
    pointAssignments = np.full_like(skeleton, -1)

    #create line list - line num: [point1, point2, ...]
    lines:list[list[int]] = []

    #create point list - point num: (x, y)
    points = []

    offsets = [-1, 0, 1]

    #create x and y indices
    #loop through array with x and y indices

    for y in range(skeleton.shape[0]):
        for x in range(skeleton.shape[1]):
            #if array = 1 and hasn't been assigned yet, add to stack
            if skeleton[y][x] == 1 and lineAssignments[y][x] == 0:
                stack.append((x, y, -1))

            #if stack empty, continue
            if len(stack) == 0:
                continue

            #stack element: (x index, y index, line index)
            #while stack not empty
            while len(stack) > 0:
                #pop first element
                pointX, pointY, lineInd = stack[0]
                del stack[0]

                if lineAssignments[pointY][pointX] == 1:
                    continue

                pointNum = len(points)

                #mark point on line
                if lineInd >= 0:
                    lines[lineInd].append(pointNum)
                else:
                    lineInd = len(lines)
                    newLine = [pointNum]
                    lines.append(newLine)

                #add point to point list
                points.append((pointX, pointY))

                #mark on point assignment array
                pointAssignments[pointY][pointX] = pointNum

                #mark on line assignment array
                lineAssignments[pointY][pointX] = 1

                #loop through neighbor offsets
                neighbors = []

                for yOffset in offsets:
                    for xOffset in offsets:
                        if pointY + yOffset < 0 or pointY + yOffset >= skeleton.shape[0]:
                            continue

                        if pointX + xOffset < 0 or pointX + xOffset >= skeleton.shape[1]:
                            continue

                        if xOffset == 0 and yOffset == 0:
                            continue

                        #count number of unassigned white pixels nearby
                        if skeleton[pointY + yOffset][pointX + xOffset] == 1 and lineAssignments[pointY + yOffset][pointX + xOffset] == 0:
                            neighbors.append((pointX + xOffset, pointY + yOffset))

                #determine if junction, unassigned white pixels nearby > 1
                isJunction = len(neighbors) > 1

                #loop through neighbors
                for neighbor in neighbors:
                    #if not junction, add to stack as an extension of the lines
                    if not isJunction:
                        stack.append((neighbor[0], neighbor[1], lineInd))
                    else:
                    #if junction, create new line, add current point as first point on the line, 
                    #add neighbor to stack as extension of that line
                        newLine = [pointNum]
                        stack.append((neighbor[0], neighbor[1], len(lines)))
                        lines.append(newLine)

    return lines, points

def RemoveShortLines(lines:list[list[int]], minLength:int) -> list[list[int]]:
    index = 0
    while index < len(lines):
        if len(lines[index]) < minLength:
            del lines[index]
            index -= 1

        index += 1

    return lines

def perpendicular_distance(point:tuple[int, int], start:tuple[int, int], end:tuple[int, int]):
    """Calculate the perpendicular distance from a point to a line segment."""
    x0, y0 = point
    x1, y1 = start
    x2, y2 = end

    if (x1, y1) == (x2, y2):
        return math.hypot(x0 - x1, y0 - y1)

    num = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2*y1 - y2*x1)
    den = math.hypot(y2 - y1, x2 - x1)
    return num / den

def rdp(points:list[tuple[int, int]], polyline:list[int], epsilon:float) -> list[int]:
    """Simplify the polyline using the RDP algorithm.

    Args:
        points: List of (x, y) tuples.
        polyline: List of indices into `points` representing the polyline.
        epsilon: Distance threshold for simplification.

    Returns:
        A simplified polyline as a list of indices into `points`.
    """
    def rdp_recursive(start_idx, end_idx):
        max_dist = 0.0
        index = None

        start_point = points[polyline[start_idx]]
        end_point = points[polyline[end_idx]]

        for i in range(start_idx + 1, end_idx):
            dist = perpendicular_distance(points[polyline[i]], start_point, end_point)
            if dist > max_dist:
                max_dist = dist
                index = i

        if max_dist > epsilon:
            # Recursive call
            left = rdp_recursive(start_idx, index)
            right = rdp_recursive(index, end_idx)
            return left[:-1] + right  # avoid duplicating index at the junction
        else:
            return [polyline[start_idx], polyline[end_idx]]

    if len(polyline) < 2:
        return polyline  # Not enough points to simplify

    return rdp_recursive(0, len(polyline) - 1)

def SimplifyLines(lines:list[list[int]], points:list[tuple[int, int]], maxDist:float) -> tuple[list, list]:
    for i in range(len(lines)):
        lines[i] = rdp(points, lines[i], maxDist)

    return lines, points

def remove_unused_points(points, lines):
    # Step 1: Find all used point indices
    used_indices = set(index for line in lines for index in line)

    # Step 2: Create a mapping from old index to new index
    index_mapping = {}
    new_points = []
    for new_idx, old_idx in enumerate(sorted(used_indices)):
        index_mapping[old_idx] = new_idx
        new_points.append(points[old_idx])

    # Step 3: Update lines to use new indices
    new_lines = [[index_mapping[idx] for idx in line] for line in lines]

    return new_lines, new_points

def NormalizePoints(points:list[tuple[int, int]], width:int, height:int) -> list[tuple[float, float]]:
    newPoints = []
    for i in range(len(points)):
        point = (points[i][0] / width, 1 - (points[i][1] / height))
        newPoints.append(point)

    return newPoints

def VectorizeSkeleton(skeleton:np.ndarray) -> tuple[list, list]:
    skeleton = np.asarray(skeleton, dtype=np.int64)
    
    #find initial lines
    lines, points = GetInitialLines(skeleton)

    lines = RemoveShortLines(lines, 5)

    points = NormalizePoints(points, skeleton.shape[1], skeleton.shape[0])

    print("Got initial lines")

    #in pixels
    maxErrorDist = 0.001
    #simplify lines
    lines, points = SimplifyLines(lines, points, maxErrorDist)

    lines, points = remove_unused_points(points, lines)

    return lines, points

def plot_points_and_lines(points, lines):
    """
    Plots a set of points and lines using matplotlib, flipped vertically with no legend.

    Parameters:
    - points: List of tuples, each representing (x, y) coordinates.
    - lines: List of lists, each containing indices of points that form a line.
    """
    # Unzip points into x and y coordinates
    x_coords, y_coords = zip(*points)
    
    # Plot all points
    plt.scatter(x_coords, y_coords, color='blue')

    # Plot each line
    for line in lines:
        line_points = [points[i] for i in line]
        line_x, line_y = zip(*line_points)
        plt.plot(line_x, line_y, marker='o')

    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Points and Lines (Flipped Vertically)')
    plt.gca().set_aspect('equal', adjustable='box')
    #plt.gca().invert_yaxis()  # Flip vertically
    plt.grid(False)
    plt.show()
