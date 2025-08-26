from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, QApplication, QTextEdit
from PySide6.QtGui import QPixmap, QColor, QResizeEvent, QDoubleValidator
from PySide6.QtCore import Qt, Signal

from collections import OrderedDict
from PIL import Image
import os
import numpy as np

from HelperFunctions import camel_case_to_capitalized, ArrayToPixmap, originalImageKey, statFunctionMap, vectorKey, pointsKey, linesKey, clusterKey, functionTypeKey, imageTypeKey, clusterTypeKey, lineTypeKey
from InteractiveSkeletonPixmap import InteractiveSkeletonPixmap
from CustomTextEdit import CustomTextEdit

class SkeletonViewer(QWidget):
    BackButtonPressed = Signal()
    #line index, line comments, cluster index, cluster comments
    CommentsChanged = Signal(str, int, str, int, str)

    def __init__(self):
        super().__init__()

        self.imageResolution = 512

        self.currentResults = None
        self.currentSkeletonKey = None
        self.currentImageName = None

        self.imageTitleLabelPrefix = "File Name: "
        self.lineLengthPrefix = "Selected Line Length: "
        self.clumpLengthPrefix = "Selected Clump Length: "

        self.AddUI()

    def AddUI(self) -> None:
        blackPixmap = QPixmap(self.imageResolution, self.imageResolution)
        blackPixmap.fill(QColor("black"))
        
        self.skeletonLabel = InteractiveSkeletonPixmap(self.imageResolution)
        self.skeletonLabel.UpdateLineComments.connect(self.ReadComments)
        self.skeletonLabel.UpdateLineData.connect(self.UpdateLengthLabels)
        self.skeletonLabel.setPixmap(blackPixmap)
        
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        
        topLayout = QHBoxLayout()
        mainLayout.addLayout(topLayout, 1)

        backButton = QPushButton("Back")
        backButton.pressed.connect(self.BackToOverview)
        topLayout.addWidget(backButton, 1)

        self.imageTitleLabel = QLabel(self.imageTitleLabelPrefix)
        topLayout.addWidget(self.imageTitleLabel, 4)

        scaleLabelLayout = QHBoxLayout()
        topLayout.addLayout(scaleLabelLayout, stretch=2)
        scaleLabelLayout.addWidget(QLabel("Image Side Length (any unit):"))
        self.imageScaleLineEdit = QLineEdit("1.0")
        scaleLabelLayout.addWidget(self.imageScaleLineEdit)
        validator = QDoubleValidator(0.0, 999, 2)
        self.imageScaleLineEdit.setValidator(validator)
        self.imageScaleLineEdit.editingFinished.connect(self.skeletonLabel.EmitLineData)

        lengthLayout = QHBoxLayout()
        mainLayout.addLayout(lengthLayout, 1)

        self.lineLengthLabel = QLabel(self.lineLengthPrefix + "N/A")
        lengthLayout.addWidget(self.lineLengthLabel)

        self.clumpLengthLabel = QLabel(self.clumpLengthPrefix + "N/A")
        lengthLayout.addWidget(self.clumpLengthLabel)

        imageLayout = QHBoxLayout()
        mainLayout.addLayout(imageLayout, 50)

        self.origImageLabel = QLabel()
        self.origImageLabel.setPixmap(blackPixmap)
        imageLayout.addWidget(self.origImageLabel)

        imageLayout.addWidget(self.skeletonLabel)

        paddedLayout = QVBoxLayout()
        imageLayout.addLayout(paddedLayout)

        statsLayout = QVBoxLayout()
        paddedLayout.addLayout(statsLayout, 1)

        self.calculationStatLabels = OrderedDict()

        for key in statFunctionMap:
            title = camel_case_to_capitalized(key)
            newLabel = QLabel(f"{title}: ")
            self.calculationStatLabels[key] = newLabel
            newLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            statsLayout.addWidget(newLabel, 1)

        self.selectedLineLabel = QLabel("Selected Line Comments (index N/A): ")
        statsLayout.addWidget(self.selectedLineLabel)

        self.selectedLineTextbox = CustomTextEdit()
        self.selectedLineTextbox.textChanged.connect(self.UpdateComments)
        self.selectedLineTextbox.setPlaceholderText("...")
        self.selectedLineTextbox.setReadOnly(True)
        statsLayout.addWidget(self.selectedLineTextbox)

        self.selectedClusterLabel = QLabel("Selected Cluster Comments (index N/A): ")
        statsLayout.addWidget(self.selectedClusterLabel)

        self.selectedClusterTextbox = CustomTextEdit()
        self.selectedClusterTextbox.textChanged.connect(self.UpdateComments)
        self.selectedClusterTextbox.setPlaceholderText("...")
        self.selectedClusterTextbox.setReadOnly(True)
        statsLayout.addWidget(self.selectedClusterTextbox)

        paddedLayout.addWidget(QWidget(), 1)

        self.changingProgrammatically = False

    def BackToOverview(self) -> None:
        self.BackButtonPressed.emit()

    def SetCurrentImage(self, result:dict) -> None:
        self.currentResults = result

    def ReadComments(self, lineIndex:int, clusterIndex:int) -> None:
        if lineIndex < 0 or clusterIndex < 0:
            self.changingProgrammatically = True
            self.selectedLineTextbox.setText("")
            self.selectedClusterTextbox.setText("")
            self.changingProgrammatically = False
            
            self.selectedLineTextbox.setReadOnly(True)
            self.selectedClusterTextbox.setReadOnly(True)

            self.selectedLineLabel.setText("Selected Line Comments (index N/A):")
            self.selectedClusterLabel.setText("Selected Cluster Comments (index N/A):")
            return
        
        self.selectedLineTextbox.setReadOnly(False)
        self.selectedClusterTextbox.setReadOnly(False)

        newSelectedLineText = f"Selected Line Comments (index {lineIndex}):"
        self.selectedLineLabel.setText(newSelectedLineText)
        self.selectedLineLabel.repaint()

        newSelectedClusterText = f"Selected Cluster Comments (index {clusterIndex}):"
        self.selectedClusterLabel.setText(newSelectedClusterText)
        self.selectedClusterLabel.repaint()

        self.changingProgrammatically = True
        #read in comments
        if str(lineIndex) in self.currentResults[self.currentSkeletonKey]["lineComments"]:
            self.selectedLineTextbox.setText(self.currentResults[self.currentSkeletonKey]["lineComments"][str(lineIndex)])
        else:
            self.selectedLineTextbox.setText("")

        if str(clusterIndex) in self.currentResults[self.currentSkeletonKey]["clusterComments"]:
            temp = self.currentResults[self.currentSkeletonKey]["clusterComments"][str(clusterIndex)]
            self.selectedClusterTextbox.setText(temp)
        else:
            self.selectedClusterTextbox.setText("")
        self.changingProgrammatically = False

    def UpdateComments(self) -> None:
        if self.changingProgrammatically:
            return
        
        if self.skeletonLabel.selectedLineIndex is None or self.skeletonLabel.selectedClumpIndex is None:
            return

        self.currentResults[self.currentSkeletonKey]["lineComments"][str(self.skeletonLabel.selectedLineIndex)] = self.selectedLineTextbox.toPlainText()
        self.currentResults[self.currentSkeletonKey]["clusterComments"][str(self.skeletonLabel.selectedClumpIndex)] = self.selectedClusterTextbox.toPlainText()

        self.CommentsChanged.emit(self.currentSkeletonKey,
                                  self.skeletonLabel.selectedLineIndex,
                                  self.selectedLineTextbox.toPlainText(),
                                  self.skeletonLabel.selectedClumpIndex,
                                  self.selectedClusterTextbox.toPlainText())

    def UpdateLengthLabels(self, lineLength:float, clumpLength:float, lineIndex:int, clumpIndex:int) -> None:
        imageScale = float(self.imageScaleLineEdit.text())
        
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
                    value = self.currentResults[self.currentSkeletonKey][statsLabelKey][clumpIndex]
                elif statFunctionMap[statsLabelKey][functionTypeKey] == lineTypeKey:
                    value = self.currentResults[self.currentSkeletonKey][statsLabelKey][lineIndex]

                if statFunctionMap[statsLabelKey]["inImageSpace"]:
                    value *= imageScale

                self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: {value}")

    def SetImage(self, imageName:str, currSkeletonKey:str) -> None:
        self.currentImageName = imageName

        self.imageTitleLabel.setText(self.imageTitleLabelPrefix + imageName)

        self.currentSkeletonKey = currSkeletonKey

        originalImage = Image.open(self.currentResults[originalImageKey])
        originalImageArray = np.asarray(originalImage, dtype=np.float64).copy()

        maxValue = np.max(originalImageArray)
        minValue = np.min(originalImageArray)
        originalImageArray -= minValue
        maxValue -= minValue
        originalImageArray /= maxValue

        originalImagePixmap = ArrayToPixmap(originalImageArray, self.imageResolution, False)
        self.skeletonLabel.SetLines(self.currentResults[currSkeletonKey][vectorKey][pointsKey], 
                                    self.currentResults[currSkeletonKey][vectorKey][linesKey], 
                                    self.currentResults[currSkeletonKey][vectorKey][clusterKey])

        self.origImageLabel.setPixmap(originalImagePixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            subtitle = f"(per {statFunctionMap[statsLabelKey][functionTypeKey]})"

            if statFunctionMap[statsLabelKey][functionTypeKey] == imageTypeKey:
                self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: {self.currentResults[currSkeletonKey][statsLabelKey]}")
            else:
                self.calculationStatLabels[statsLabelKey].setText(f"{title} {subtitle}: N/A")

    def resizeEvent(self, event:QResizeEvent):
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        if event.size().width() > screen_rect.width():
            event.size().setWidth(screen_rect.width())

        if event.size().height() > screen_rect.height():
            event.size().setHeight(screen_rect.height())

        return super().resizeEvent(event)