from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

import numpy as np

from functools import partial
from collections import OrderedDict

import os
import json

from PIL import Image

from CreateSkeleton import generate_skeletonized_images
from HelperFunctions import camel_case_to_capitalized, draw_lines_on_pixmap, ArrayToPixmap, NormalizeImageArray, skeletonKey, originalImageKey, statFunctionMap, vectorKey, pointsKey, linesKey, functionTypeKey, imageTypeKey
from ClickableLabel import ClickableLabel

class ImageOverview(QWidget):
    ClickedOnSkeleton = Signal(str)
    GeneratedResults = Signal(OrderedDict)

    def __init__(self) -> None:
        super().__init__()

        self.currentResults = OrderedDict()
        self.currentIndex = 0

        self.imageTitleLabelPrefix = "File Name: "

        self.workingDirectory = os.getcwd()

        self.createdSkeletons = False
        self.skeletonUIAdded = False

        self.defaultInputDirectory = ""
        self.defaultOutputDirectory = ""

        self.statsFileName = "calculations.json"

        self.initSettingsFilePath = os.path.join(self.workingDirectory, "initializationSettings.json")

        self.defaultInputDirectory = os.path.join(self.workingDirectory, "Images")
        self.defaultOutputDirectory = os.path.join(self.workingDirectory, "Skeletons")

        if os.path.exists(self.initSettingsFilePath):
            self.LoadInitializationSettings()
        else:
            self.CreateInitializationSettings()

        self.CreateUI()

    def CreateUI(self):
        # Set window title and size
        self.setWindowTitle("Fungal Structure Detector")
        self.setGeometry(100, 100, 600, 200)

        # Layout
        self.mainLayout = QHBoxLayout()
        self.setLayout(self.mainLayout)

        buttonLayout = QVBoxLayout()
        self.mainLayout.addLayout(buttonLayout)

        self.AddButtonUI(buttonLayout)

    def AddButtonUI(self, layout:QVBoxLayout|QHBoxLayout) -> None:
        inputDirLayout = QHBoxLayout()
        layout.addLayout(inputDirLayout)
        inputDirLabel = QPushButton("Input Directory:")
        inputDirLayout.addWidget(inputDirLabel)
        self.inputDirLineEdit = QLineEdit()
        self.inputDirLineEdit.setPlaceholderText("...")
        self.inputDirLineEdit.setText(self.defaultInputDirectory)
        inputDirLayout.addWidget(self.inputDirLineEdit)

        inputDirLabel.clicked.connect(partial(self.SelectDirectoryAndSetLineEdit, self.inputDirLineEdit))

        outputDirLayout = QHBoxLayout()
        layout.addLayout(outputDirLayout)
        outputDirLabel = QPushButton("Output Directory:")
        outputDirLayout.addWidget(outputDirLabel)
        self.outputDirLineEdit = QLineEdit()
        self.outputDirLineEdit.setPlaceholderText("...")
        self.outputDirLineEdit.setText(self.defaultOutputDirectory)
        outputDirLayout.addWidget(self.outputDirLineEdit)

        outputDirLabel.clicked.connect(partial(self.SelectDirectoryAndSetLineEdit, self.outputDirLineEdit))

        generateSkeletonsButton = QPushButton("Generate Skeletons")
        generateSkeletonsButton.clicked.connect(self.GenerateSkeletons)
        layout.addWidget(generateSkeletonsButton)

    def GenerateSkeletons(self) -> None:
        self.createdSkeletons = True
        
        inputDir = self.inputDirLineEdit.text()
        outputDir = self.outputDirLineEdit.text()

        self.defaultInputDirectory = inputDir
        self.defaultOutputDirectory = outputDir
        self.CreateInitializationSettings()

        result = generate_skeletonized_images(inputDir)

        jsonFileResult = {}

        for fileName in result:
            baseFileName, extension = os.path.splitext(fileName)

            newBaseFileName = baseFileName + "_skeleton"
            newFileName = newBaseFileName + extension

            imgArray = result[fileName][skeletonKey]
            img = Image.fromarray(np.asarray(imgArray * 255, dtype=np.uint8), mode="L")
            img = img.convert("RGB")
            img.save(os.path.join(outputDir, newFileName))

            jsonElement = {}
            for key in result[fileName]:
                if key == originalImageKey or key == skeletonKey:
                    continue

                jsonElement[key] = result[fileName][key]

            jsonFileResult[fileName] = jsonElement

        self.currentResults = result

        jsonFilePath = os.path.join(self.outputDirLineEdit.text(), self.statsFileName)
        jsonFile = open(jsonFilePath, "w")
        json.dump(jsonFileResult, jsonFile, indent=4)
        jsonFile.close()

        self.AddSkeletonUI()

        self.GeneratedResults.emit(self.currentResults)

    def AddSkeletonUI(self) -> None:
        if self.skeletonUIAdded:
            self.LoadImageIntoUI(0)
            return
        
        self.skeletonUIAdded = True
        
        self.resize(1000, 500)

        skeletonLayout = QVBoxLayout()
        self.mainLayout.addLayout(skeletonLayout)

        self.imageTitleLabel = QLabel(self.imageTitleLabelPrefix)
        self.imageTitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        skeletonLayout.addWidget(self.imageTitleLabel)

        middleSkeletonLayout = QHBoxLayout()
        skeletonLayout.addLayout(middleSkeletonLayout)

        imageLayout = QVBoxLayout()
        middleSkeletonLayout.addLayout(imageLayout)
        
        self.originalImageLabel = QLabel()
        self.skeletonLabel = ClickableLabel()
        self.skeletonLabel.clicked.connect(self.GoIntoSkeletonView)

        imageLayout.addWidget(self.originalImageLabel)
        imageLayout.addWidget(self.skeletonLabel)

        self.originalImageLabel.setPixmap(QPixmap(256, 256))
        self.skeletonLabel.setPixmap(QPixmap(256, 256))

        statsLayout = QVBoxLayout()
        middleSkeletonLayout.addLayout(statsLayout)

        self.calculationStatLabels = OrderedDict()

        for key in statFunctionMap:
            if statFunctionMap[key][functionTypeKey] != imageTypeKey:
                continue

            title = camel_case_to_capitalized(key)
            newLabel = QLabel(f"{title}: ")
            self.calculationStatLabels[key] = newLabel
            newLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            statsLayout.addWidget(newLabel)

        scrollButtonLayout = QHBoxLayout()
        skeletonLayout.addLayout(scrollButtonLayout)
        self.leftButton = QPushButton("🠨")
        font = self.leftButton.font()
        font.setPointSize(25)
        self.leftButton.setFont(font)
        scrollButtonLayout.addWidget(self.leftButton)
        self.leftButton.clicked.connect(partial(self.ChangeIndex, -1))

        self.leftButton.setEnabled(False)

        self.rightButton = QPushButton("🠪")
        font = self.rightButton.font()
        font.setPointSize(25)
        self.rightButton.setFont(font)
        scrollButtonLayout.addWidget(self.rightButton)
        self.rightButton.clicked.connect(partial(self.ChangeIndex, 1))

        self.LoadImageIntoUI(0)

    def GoIntoSkeletonView(self) -> None:
        self.ClickedOnSkeleton.emit(list(self.currentResults.keys())[self.currentIndex])

    def LoadImageIntoUI(self, index:int) -> None:
        self.currentIndex = index

        imageFileName = list(self.currentResults.keys())[index]

        self.imageTitleLabel.setText(self.imageTitleLabelPrefix + imageFileName)

        originalImagePixmap = ArrayToPixmap(self.currentResults[imageFileName][originalImageKey], 256, False)
        skeletonPixmap = draw_lines_on_pixmap(self.currentResults[imageFileName][vectorKey][pointsKey], self.currentResults[imageFileName][vectorKey][linesKey], 256)

        self.originalImageLabel.setPixmap(originalImagePixmap)
        self.skeletonLabel.setPixmap(skeletonPixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            self.calculationStatLabels[statsLabelKey].setText(f"{title}: {self.currentResults[imageFileName][statsLabelKey]}")

    def ChangeIndex(self, direction:int) -> None:
        if self.currentIndex + direction < 0 or self.currentIndex + direction >= len(self.currentResults):
            return
        
        self.LoadImageIntoUI(self.currentIndex + direction)

        if self.currentIndex == 0:
            self.leftButton.setEnabled(False)
        elif not self.leftButton.isEnabled():
            self.leftButton.setEnabled(True)

        if self.currentIndex == len(self.currentResults) - 1:
            self.rightButton.setEnabled(False)
        elif not self.rightButton.isEnabled():
            self.rightButton.setEnabled(True)

    def SelectDirectoryAndSetLineEdit(self, lineEdit:QLineEdit) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        if directory:
            directory = directory.replace("/", "\\")
            lineEdit.setText(directory)

    def LoadPreviousResults(self) -> None:
        if not os.path.exists(self.defaultInputDirectory):
            return
        
        if not os.path.exists(self.defaultOutputDirectory):
            return
        
        if not os.path.exists(os.path.join(self.defaultOutputDirectory, self.statsFileName)):
            return
        
        #load stats in
        statsFile = open(os.path.join(self.defaultOutputDirectory, self.statsFileName), "r")
        stats = json.load(statsFile)
        statsFile.close()

        self.currentResults = OrderedDict()

        #create dict and loop through original images
        for origImageFileName in stats:
            if not os.path.exists(os.path.join(self.defaultInputDirectory, origImageFileName)):
                continue
            
            if origImageFileName not in stats:
                continue

            origFileBaseName, origFileExtension = os.path.splitext(origImageFileName)

            skeletonFileName = f"{origFileBaseName}_skeleton{origFileExtension}"

            if not os.path.exists(os.path.join(self.defaultOutputDirectory, skeletonFileName)):
                continue

            currEntry = {}

            #load orig image, normalize it to 0-1
            origImage = Image.open(os.path.join(self.defaultInputDirectory, origImageFileName))
            origImageArray = np.asarray(origImage, dtype=np.float64)
            origImageArray = NormalizeImageArray(origImageArray)

            currEntry[originalImageKey] = origImageArray

            #load skeleton, normalize it to 0-1
            skeletonImage = Image.open(os.path.join(self.defaultOutputDirectory, skeletonFileName))
            skeletonArray = np.asarray(skeletonImage, dtype=np.float64)
            skeletonArray = NormalizeImageArray(skeletonArray)

            currEntry[skeletonKey] = skeletonArray

            currEntry[vectorKey] = stats[origImageFileName][vectorKey]

            #add in stats
            for statsKey in statFunctionMap:
                if statsKey not in stats[origImageFileName]:
                    currEntry[statsKey] = None
                else:
                    currEntry[statsKey] = stats[origImageFileName][statsKey]

            self.currentResults[origImageFileName] = currEntry

        self.AddSkeletonUI()

        self.GeneratedResults.emit(self.currentResults)

    def CreateInitializationSettings(self) -> None:
        self.defaultInputDirectory = self.defaultInputDirectory.replace("/", "\\")
        self.defaultOutputDirectory = self.defaultOutputDirectory.replace("/", "\\")
        
        initializationSettings = {
            "defaultInputDirectory": self.defaultInputDirectory,
            "defaultOutputDirectory": self.defaultOutputDirectory
        }

        initFile = open(self.initSettingsFilePath, "w")
        json.dump(initializationSettings, initFile, indent=4)
        initFile.close()

    def LoadInitializationSettings(self):
        initFile = open(self.initSettingsFilePath, "r")
        initSettings = json.load(initFile)
        initFile.close()

        self.defaultInputDirectory = initSettings["defaultInputDirectory"]
        self.defaultOutputDirectory = initSettings["defaultOutputDirectory"]