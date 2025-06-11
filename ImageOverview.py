from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, QComboBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

import numpy as np

from functools import partial
from collections import OrderedDict

import os
import json

from PIL import Image

from CreateSkeleton import generate_skeletonized_images
from HelperFunctions import camel_case_to_capitalized, draw_lines_on_pixmap, ArrayToPixmap, NormalizeImageArray, skeletonKey, originalImageKey, statFunctionMap, vectorKey, pointsKey, linesKey, functionTypeKey, imageTypeKey, timestampKey, sampleKey
from ClickableLabel import ClickableLabel

class ImageOverview(QWidget):
    ClickedOnSkeleton = Signal(str)
    LoadedNewImage = Signal(dict)

    def __init__(self) -> None:
        super().__init__()

        self.currentIndex = 0

        self.imageTitleLabelPrefix = "File Name: "

        self.workingDirectory = os.getcwd()

        self.createdSkeletons = False
        self.skeletonUIAdded = False

        self.defaultInputDirectory = ""
        self.defaultOutputDirectory = ""

        self.initSettingsFilePath = os.path.join(self.workingDirectory, "initializationSettings.json")

        self.defaultInputDirectory = os.path.join(self.workingDirectory, "Images")
        self.defaultOutputDirectory = os.path.join(self.workingDirectory, "Skeletons")

        self.sampleToFiles = {}
        self.currentFileList = []

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

        #create sample map based on input directory
        self.GetSamples(inputDir)

        if not os.path.exists(os.path.join(outputDir, "Calculations")):
            os.makedirs(os.path.join(outputDir, "Calculations"))

        #loop through samples/files
        for sample in self.sampleToFiles:
            for fileName in self.sampleToFiles[sample]:
                #get result from skeleton creator
                result = generate_skeletonized_images(inputDir, fileName)

                #save skeleton image file
                baseFileName, extension = os.path.splitext(fileName)

                newBaseFileName = baseFileName + "_skeleton"
                newFileName = newBaseFileName + extension

                result[originalImageKey] = os.path.join(inputDir, fileName)

                imgArray = result[skeletonKey]
                img = Image.fromarray(np.asarray(imgArray * 255, dtype=np.uint8), mode="L")
                img = img.convert("RGB")
                img.save(os.path.join(outputDir, newFileName))

                #save JSON file for image
                fileNameSplit:list[str] = os.path.splitext(fileName)[0].split("_")
                timestamp = int(fileNameSplit[-1])

                result[timestampKey] = timestamp
                result[sampleKey] = sample

                jsonElement = {}
                for key in result:
                    jsonElement[key] = result[key]

                jsonElement[originalImageKey] = os.path.join(inputDir, fileName)
                jsonElement[skeletonKey] = os.path.join(outputDir, newFileName)

                jsonFilePath = os.path.join(self.outputDirLineEdit.text(), "Calculations", baseFileName + "_calculations.json")
                jsonFile = open(jsonFilePath, "w")
                json.dump(jsonElement, jsonFile, indent=4)
                jsonFile.close()

        #add skeleton UI
        self.AddSkeletonUI()

    def AddSkeletonUI(self) -> None:
        if self.skeletonUIAdded:
            self.LoadImageIntoUI(0)
            return
        
        self.skeletonUIAdded = True
        
        self.resize(1000, 500)

        skeletonLayout = QVBoxLayout()
        self.mainLayout.addLayout(skeletonLayout)

        self.sampleDropdown = QComboBox()
        self.sampleDropdown.addItems(list(self.sampleToFiles.keys()))
        self.sampleDropdown.currentTextChanged.connect(self.LoadNewSample)
        self.sampleDropdown.setCurrentIndex(0)
        skeletonLayout.addWidget(self.sampleDropdown)

        self.timestampLabel = QLabel("Timestamp: N/A")
        self.timestampLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        skeletonLayout.addWidget(self.timestampLabel)

        middleSkeletonLayout = QHBoxLayout()
        skeletonLayout.addLayout(middleSkeletonLayout)

        imageLayout = QVBoxLayout()
        middleSkeletonLayout.addLayout(imageLayout)
        
        self.originalImageLabel = ClickableLabel()
        self.originalImageLabel.clicked.connect(self.GoIntoSkeletonView)
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

        self.LoadNewSample(list(self.sampleToFiles.keys())[0])

    def LoadNewSample(self, value:str) -> None:
        self.currentFileList = self.sampleToFiles[value]

        self.LoadImageIntoUI(0)

    def GoIntoSkeletonView(self) -> None:
        self.ClickedOnSkeleton.emit(self.currentFileList[self.currentIndex])

    def LoadImageIntoUI(self, index:int) -> None:
        self.currentIndex = index

        imageFileName = self.currentFileList[index]

        #load calculation file
        calculationFileName = os.path.splitext(imageFileName)[0] + "_calculations.json"
        calculationFilePath = os.path.join(self.defaultOutputDirectory, "Calculations", calculationFileName)

        calculationFile = open(calculationFilePath, "r")
        calculations = json.load(calculationFile)
        calculationFile.close()

        self.timestampLabel.setText(f"Timestamp: {calculations[timestampKey]}")

        originalImage = Image.open(os.path.join(self.defaultInputDirectory, imageFileName))
        originalImageArray = np.asarray(originalImage, dtype=np.float64).copy()

        maxValue = np.max(originalImageArray)
        minValue = np.min(originalImageArray)
        originalImageArray -= minValue
        maxValue -= minValue
        originalImageArray /= maxValue

        originalImagePixmap = ArrayToPixmap(originalImageArray, 256, False)
        skeletonPixmap = draw_lines_on_pixmap(calculations[vectorKey][pointsKey], calculations[vectorKey][linesKey], 256)

        self.originalImageLabel.setPixmap(originalImagePixmap)
        self.skeletonLabel.setPixmap(skeletonPixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            self.calculationStatLabels[statsLabelKey].setText(f"{title}: {calculations[statsLabelKey]}")

        self.LoadedNewImage.emit(calculations)

    def ChangeIndex(self, direction:int) -> None:
        if self.currentIndex + direction < 0 or self.currentIndex + direction >= len(self.currentFileList):
            return
        
        self.LoadImageIntoUI(self.currentIndex + direction)

        if self.currentIndex == 0:
            self.leftButton.setEnabled(False)
        elif not self.leftButton.isEnabled():
            self.leftButton.setEnabled(True)

        if self.currentIndex == len(self.currentFileList) - 1:
            self.rightButton.setEnabled(False)
        elif not self.rightButton.isEnabled():
            self.rightButton.setEnabled(True)

    def SelectDirectoryAndSetLineEdit(self, lineEdit:QLineEdit) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        if directory:
            directory = directory.replace("\\", "/")
            lineEdit.setText(directory)

    def LoadPreviousResults(self) -> None:
        if not os.path.exists(self.defaultInputDirectory):
            return
        
        if not os.path.exists(self.defaultOutputDirectory):
            return
        
        if len(os.listdir(self.defaultOutputDirectory)) < len(os.listdir(self.defaultInputDirectory)):
            return
            
        self.GetSamples(self.defaultInputDirectory)

        self.AddSkeletonUI()

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

    def GetSamples(self, inputDirectory:str) -> None:
        fileNames = os.listdir(inputDirectory)
        
        for fileName in fileNames:
            fileNameParts = os.path.splitext(fileName)[0].split("_")
            del fileNameParts[-1]

            sampleName = "_".join(fileNameParts)

            if sampleName not in self.sampleToFiles:
                self.sampleToFiles[sampleName] = [fileName]
            else:
                self.sampleToFiles[sampleName].append(fileName)

    def LoadInitializationSettings(self):
        initFile = open(self.initSettingsFilePath, "r")
        initSettings = json.load(initFile)
        initFile.close()

        self.defaultInputDirectory = initSettings["defaultInputDirectory"]
        self.defaultOutputDirectory = initSettings["defaultOutputDirectory"]