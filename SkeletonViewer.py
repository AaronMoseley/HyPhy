from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, Signal

from collections import OrderedDict
from PIL import Image
import os
import numpy as np

from HelperFunctions import camel_case_to_capitalized, ArrayToPixmap, originalImageKey, statFunctionMap, vectorKey, pointsKey, linesKey, clusterKey, functionTypeKey, imageTypeKey, clusterTypeKey, lineTypeKey
from InteractiveSkeletonPixmap import InteractiveSkeletonPixmap

class SkeletonViewer(QWidget):
    BackButtonPressed = Signal()

    def __init__(self):
        super().__init__()

        self.imageResolution = 512

        self.currentResults = None
        self.currentImageName = None

        self.imageTitleLabelPrefix = "File Name: "
        self.lineLengthPrefix = "Selected Line Length: "
        self.clumpLengthPrefix = "Selected Clump Length: "

        self.AddUI()

    def AddUI(self) -> None:
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        topLayout = QHBoxLayout()
        mainLayout.addLayout(topLayout)

        backButton = QPushButton("Back")
        backButton.pressed.connect(self.BackToOverview)
        topLayout.addWidget(backButton)

        self.imageTitleLabel = QLabel(self.imageTitleLabelPrefix)
        topLayout.addWidget(self.imageTitleLabel)

        lengthLayout = QHBoxLayout()
        mainLayout.addLayout(lengthLayout)

        self.lineLengthLabel = QLabel(self.lineLengthPrefix + "N/A")
        lengthLayout.addWidget(self.lineLengthLabel)

        self.clumpLengthLabel = QLabel(self.clumpLengthPrefix + "N/A")
        lengthLayout.addWidget(self.clumpLengthLabel)

        imageLayout = QHBoxLayout()
        mainLayout.addLayout(imageLayout)

        blackPixmap = QPixmap(self.imageResolution, self.imageResolution)
        blackPixmap.fill(QColor("black"))

        self.origImageLabel = QLabel()
        self.origImageLabel.setPixmap(blackPixmap)
        imageLayout.addWidget(self.origImageLabel)

        self.skeletonLabel = InteractiveSkeletonPixmap(self.imageResolution)
        self.skeletonLabel.PolylineHighlighted.connect(self.UpdateLengthLabels)
        self.skeletonLabel.setPixmap(blackPixmap)
        imageLayout.addWidget(self.skeletonLabel)

        statsLayout = QVBoxLayout()
        imageLayout.addLayout(statsLayout)

        self.calculationStatLabels = OrderedDict()

        for key in statFunctionMap:
            title = camel_case_to_capitalized(key)
            newLabel = QLabel(f"{title}: ")
            self.calculationStatLabels[key] = newLabel
            newLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            statsLayout.addWidget(newLabel)

    def BackToOverview(self) -> None:
        self.BackButtonPressed.emit()

    def SetCurrentImage(self, result:dict) -> None:
        self.currentResults = result

    def UpdateLengthLabels(self, lineLength:float, clumpLength:float, lineIndex:int, clumpIndex:int) -> None:
        if lineLength < 0 or clumpLength < 0:
            self.lineLengthLabel.setText(self.lineLengthPrefix + "N/A")
            self.clumpLengthLabel.setText(self.clumpLengthPrefix + "N/A")

            for statsLabelKey in self.calculationStatLabels:
                if statFunctionMap[statsLabelKey][functionTypeKey] == imageTypeKey:
                    continue

                title = camel_case_to_capitalized(statsLabelKey)

                subtitle = f"(per {statFunctionMap[statsLabelKey][functionTypeKey]})"

                self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: N/A")
        else:
            self.lineLengthLabel.setText(self.lineLengthPrefix + str(lineLength))
            self.clumpLengthLabel.setText(self.clumpLengthPrefix + str(clumpLength))

            for statsLabelKey in self.calculationStatLabels:
                if statFunctionMap[statsLabelKey][functionTypeKey] == imageTypeKey:
                    continue

                title = camel_case_to_capitalized(statsLabelKey)

                subtitle = f"(per {statFunctionMap[statsLabelKey][functionTypeKey]})"

                if statFunctionMap[statsLabelKey][functionTypeKey] == clusterTypeKey:
                    self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: {self.currentResults[statsLabelKey][clumpIndex]}")
                elif statFunctionMap[statsLabelKey][functionTypeKey] == lineTypeKey:
                    self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: {self.currentResults[statsLabelKey][lineIndex]}")

    def SetImage(self, imageName:str) -> None:
        self.currentImageName = imageName

        self.imageTitleLabel.setText(self.imageTitleLabelPrefix + imageName)

        originalImage = Image.open(self.currentResults[originalImageKey])
        originalImageArray = np.asarray(originalImage, dtype=np.float64).copy()

        maxValue = np.max(originalImageArray)
        minValue = np.min(originalImageArray)
        originalImageArray -= minValue
        maxValue -= minValue
        originalImageArray /= maxValue

        originalImagePixmap = ArrayToPixmap(originalImageArray, self.imageResolution, False)
        self.skeletonLabel.SetLines(self.currentResults[vectorKey][pointsKey], 
                                    self.currentResults[vectorKey][linesKey], 
                                    self.currentResults[vectorKey][clusterKey])

        self.origImageLabel.setPixmap(originalImagePixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            subtitle = f"(per {statFunctionMap[statsLabelKey][functionTypeKey]})"

            if statFunctionMap[statsLabelKey][functionTypeKey] == imageTypeKey:
                self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: {self.currentResults[statsLabelKey]}")
            else:
                self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: N/A")