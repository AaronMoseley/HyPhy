import csv
import os
from HelperFunctions import skeletonKey, pointsKey, linesKey, clusterKey, statFunctionMap, vectorKey, functionTypeKey, imageTypeKey, lineTypeKey, clusterTypeKey

def GenerateCSVs(jsonObject:dict, baseFileName:str, outputDirectory:str) -> None:
    #create new directory
    currentCSVDirectory = os.path.join(outputDirectory, "Calculations", baseFileName + "_skeleton_csvs")
    os.makedirs(currentCSVDirectory, exist_ok=True)

    #create csv for base file info
        #original file name
        #sample
        #timestamp
        #different skeleton file names
    baseCSVPath = os.path.join(currentCSVDirectory, "fileInfo.csv")
    baseCSVData = []

    skeletonTypes = []

    for key in jsonObject:
        if not isinstance(jsonObject[key], dict):
            baseCSVData.append([key, jsonObject[key]])
        elif skeletonKey in jsonObject[key]:
            skeletonTypes.append(key)
            baseCSVData.append([key, jsonObject[key][skeletonKey]])

    WriteCSV(baseCSVData, baseCSVPath)

    #loop through each skeleton
    for skeletonType in skeletonTypes:
        #create csv for points
        pointCSVPath = os.path.join(currentCSVDirectory, f"{skeletonType}_points.csv")
        pointData = [
            ["pointIndex", "x", "y"]
        ]

        for i, point in enumerate(jsonObject[skeletonType][vectorKey][pointsKey]):
            pointData.append([i, point[0], point[1]])

        WriteCSV(pointData, pointCSVPath)

        #create csv for line segments
        linesCSVPath = os.path.join(currentCSVDirectory, f"{skeletonType}_lines.csv")
        lineData = [
            ["lineIndex", "pointIndices..."]
        ]

        for i, lineSegment in enumerate(jsonObject[skeletonType][vectorKey][linesKey]):
            lineData.append([i] + lineSegment)

        WriteCSV(lineData, linesCSVPath)

        #create csv for clusters
        clusterCSVPath = os.path.join(currentCSVDirectory, f"{skeletonType}_clusters.csv")
        clusterData = [
            ["clusterIndex", "lineIndices..."]
        ]

        for i, cluster in enumerate(jsonObject[skeletonType][vectorKey][clusterKey]):
            clusterData.append([i] + cluster)

        WriteCSV(clusterData, clusterCSVPath)

        #create csv for metadata
        metadataCSVPath = os.path.join(currentCSVDirectory, f"{skeletonType}_metadata.csv")
        metadataData = [
            ["name", "value", "lineIndex", "clusterIndex"]
        ]

        for statFunctionKey in statFunctionMap:
            if not isinstance(jsonObject[skeletonType][statFunctionKey], list) or statFunctionMap[statFunctionKey][functionTypeKey] == imageTypeKey:
                metadataData.append([statFunctionKey, jsonObject[skeletonType][statFunctionKey], "", ""])
                continue

            if statFunctionMap[statFunctionKey][functionTypeKey] == imageTypeKey:
                continue

            for i, value in enumerate(jsonObject[skeletonType][statFunctionKey]):
                line = [statFunctionKey, value]

                if statFunctionMap[statFunctionKey][functionTypeKey] == lineTypeKey:
                    line.append(i)
                    line.append("")
                else:
                    line.append("")
                    line.append(i)

                metadataData.append(line)
        
        WriteCSV(metadataData, metadataCSVPath)

def WriteCSV(data:list, path:str) -> None:
    with open(path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)