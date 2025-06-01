import numpy as np
from tqdm import tqdm
import time

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

def SimplifyLines(lines:list[list[int]], points:list[tuple[int, int]], maxDist:float) -> tuple[list, list]:
    pass

def VectorizeSkeleton(skeleton:np.ndarray) -> tuple[list, list]:
    skeleton = np.asarray(skeleton, dtype=np.int64)
    
    #find initial lines
    lines, points = GetInitialLines(skeleton)

    print("Got initial lines")

    #in pixels
    maxErrorDist = 10
    #simplify lines
    lines, points = SimplifyLines(lines, points, maxErrorDist)

    return lines, points