from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, Signal

from collections import OrderedDict

from HelperFunctions import camel_case_to_capitalized, draw_lines_on_pixmap, ArrayToPixmap, NormalizeImageArray, skeletonKey, originalImageKey, statFunctionMap, vectorKey, pointsKey, linesKey
from InteractiveSkeletonPixmap import InteractiveSkeletonPixmap

class SkeletonViewer(QWidget):
    BackButtonPressed = Signal()

    def __init__(self):
        super().__init__()

        self.imageResolution = 512

        self.currentResults = None
        self.currentImageName = None

        self.imageTitleLabelPrefix = "File Name: "

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

        imageLayout = QHBoxLayout()
        mainLayout.addLayout(imageLayout)

        blackPixmap = QPixmap(self.imageResolution, self.imageResolution)
        blackPixmap.fill(QColor("black"))

        self.origImageLabel = QLabel()
        self.origImageLabel.setPixmap(blackPixmap)
        imageLayout.addWidget(self.origImageLabel)

        self.skeletonLabel = InteractiveSkeletonPixmap()
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

    def SetCurrentResults(self, result:OrderedDict) -> None:
        self.currentResults = result

    def SetImage(self, imageName:str) -> None:
        self.currentImageName = imageName

        self.imageTitleLabel.setText(self.imageTitleLabelPrefix + imageName)

        originalImagePixmap = ArrayToPixmap(self.currentResults[imageName][originalImageKey], self.imageResolution, False)
        skeletonPixmap = draw_lines_on_pixmap(self.currentResults[imageName][vectorKey][pointsKey], self.currentResults[imageName][vectorKey][linesKey], self.imageResolution)

        self.origImageLabel.setPixmap(originalImagePixmap)
        self.skeletonLabel.setPixmap(skeletonPixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            self.calculationStatLabels[statsLabelKey].setText(f"{title}: {self.currentResults[imageName][statsLabelKey]}")