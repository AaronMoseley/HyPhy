from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, QComboBox, QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

import numpy as np

from functools import partial

import os
import json

from PIL import Image

from HelperFunctions import draw_lines_on_pixmap, ArrayToPixmap, skeletonKey, originalImageKey, vectorKey, pointsKey, linesKey, timestampKey, sampleKey, NormalizeImageArray
from ClickableLabel import ClickableLabel
from SliderLineEditCombo import SliderLineEditCombo
from ProgressBar import ProgressBarPopup

class PreviewWindow(QWidget):
    BackToOverview = Signal()
    ParametersChanged = Signal(dict, str)

    def __init__(self, skeletonMap:dict):
        super().__init__()

        self.skeletonMap = skeletonMap

        self.currentStepIndex:int = 0
        self.currentSkeletonLabel:str = ""

        self.originalImageArray:np.ndarray = None

        self.sliders = {}

        self.CreateUI()

    def CreateUI(self) -> None:
        #overall, horizontal QBox
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)

        #left VQBox, contains image name and parameter sliders
        leftLayout = QVBoxLayout()
        mainLayout.addLayout(leftLayout)

        backButton = QPushButton("Back")
        leftLayout.addWidget(backButton)
        backButton.clicked.connect(self.BackToOverview.emit)

        self.imageNameLabel = QLabel("Image: N/A")
        leftLayout.addWidget(self.imageNameLabel)

        self.parameterLayout = QVBoxLayout()
        leftLayout.addLayout(self.parameterLayout)

        #right VQBox, contains name of step, related parameters, original image pixmap, skeleton pixmap, right/left buttons
        rightLayout = QVBoxLayout()
        mainLayout.addLayout(rightLayout)

        self.stepNameLabel = QLabel("Current Step: N/A")
        rightLayout.addWidget(self.stepNameLabel)

        self.relevantParametersLabel = QLabel("Related Parameters:")
        rightLayout.addWidget(self.relevantParametersLabel)

        self.mainImageLabel = QLabel()
        mainImagePixmap = QPixmap(256, 256)
        self.mainImageLabel.setPixmap(mainImagePixmap)
        rightLayout.addWidget(self.mainImageLabel)

        self.skeletonLabel = QLabel()
        skeletonPixmap = QPixmap(256, 256)
        self.skeletonLabel.setPixmap(skeletonPixmap)
        rightLayout.addWidget(self.skeletonLabel)

        scrollButtonLayout = QHBoxLayout()
        rightLayout.addLayout(scrollButtonLayout)
        self.leftButton = QPushButton("🠨")
        font = self.leftButton.font()
        font.setPointSize(25)
        self.leftButton.setFont(font)
        scrollButtonLayout.addWidget(self.leftButton)
        #self.leftButton.clicked.connect(partial(self.ChangeIndex, -1))

        self.leftButton.setEnabled(False)

        self.rightButton = QPushButton("🠪")
        font = self.rightButton.font()
        font.setPointSize(25)
        self.rightButton.setFont(font)
        scrollButtonLayout.addWidget(self.rightButton)
        #self.rightButton.clicked.connect(partial(self.ChangeIndex, 1))

    def LoadNewImage(self, imagePath:str, currSkeletonKey:str, parameterValues:dict) -> None:
        #load image name and create all the sliders
        
        self.currentStepIndex = 0
        self.currentSkeletonLabel = currSkeletonKey

        self.AddParameterSliders(parameterValues)

        origImg = Image.open(imagePath)
        origImgArray = np.asarray(origImg, dtype=np.float64)
        origImgArray = NormalizeImageArray(origImgArray)
        origImgPixmap = ArrayToPixmap(origImgArray, 256)
        self.mainImageLabel.setPixmap(origImgPixmap)

    def deleteItemsOfLayout(self, layout:(QVBoxLayout | QHBoxLayout)):
     if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                self.deleteItemsOfLayout(item.layout())

    def TriggerParameterChanged(self) -> None:
        self.ParametersChanged.emit(self.sliders, self.currentSkeletonLabel)

    def AddParameterSliders(self, parameterValues:dict) -> None:
        self.deleteItemsOfLayout(self.parameterLayout)

        self.sliders = {}
        currentEntry = {}

        #loop through each parameter
        for parameterKey in parameterValues[self.currentSkeletonLabel]:
            name = self.skeletonMap[self.currentSkeletonLabel]["parameters"][parameterKey]["name"]
            defaultVal = parameterValues[self.currentSkeletonLabel][parameterKey]
            minVal = self.skeletonMap[self.currentSkeletonLabel]["parameters"][parameterKey]["min"]
            maxVal = self.skeletonMap[self.currentSkeletonLabel]["parameters"][parameterKey]["max"]
            decimals = self.skeletonMap[self.currentSkeletonLabel]["parameters"][parameterKey]["decimals"]

            slider = SliderLineEditCombo(name, defaultVal, minVal, maxVal, decimals)
            self.parameterLayout.addLayout(slider)

            slider.ValueChanged.connect(self.TriggerParameterChanged)

            currentEntry[parameterKey] = slider

        self.sliders[self.currentSkeletonLabel] = currentEntry