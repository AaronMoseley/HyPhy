from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, QComboBox, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, Signal

import numpy as np

from functools import partial

import os
import json

from PIL import Image

from HelperFunctions import draw_lines_on_pixmap, ArrayToPixmap, skeletonKey, originalImageKey, vectorKey, pointsKey, linesKey, timestampKey, sampleKey
from ClickableLabel import ClickableLabel
from SliderLineEditCombo import SliderLineEditCombo
from ProgressBar import ProgressBarPopup

class ImageOverview(QWidget):
    ClickedOnSkeleton = Signal(str, str)
    LoadedNewImage = Signal(dict)
    ParametersChanged = Signal(dict, str)
    TriggerPreview = Signal(str, str)

    def __init__(self, skeletonMap:dict) -> None:
        super().__init__()

        self.skeletonMap = skeletonMap

        self.imageSize = 256

        self.currentIndex = 0

        self.imageTitleLabelPrefix = "File Name: "

        self.workingDirectory = os.getcwd()

        self.createdSkeletons = False
        self.skeletonUIAdded = False

        self.defaultInputDirectory = ""
        self.defaultOutputDirectory = ""

        self.currentSample = ""

        self.initSettingsFilePath = os.path.join(self.workingDirectory, "initializationSettings.json")

        self.defaultInputDirectory = os.path.join(self.workingDirectory, "Images")
        self.defaultOutputDirectory = os.path.join(self.workingDirectory, "Skeletons")

        self.currentSkeletonsOverlayed = set()

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

        generateSkeletonsButton = QPushButton("Generate All Skeletons")
        generateSkeletonsButton.clicked.connect(self.GenerateSkeletons)
        layout.addWidget(generateSkeletonsButton)

        self.generateIndividualSkeletonButton = QPushButton("Generate Single Skeleton")
        self.generateIndividualSkeletonButton.clicked.connect(self.GenerateSingleSkeleton)
        layout.addWidget(self.generateIndividualSkeletonButton)
        self.generateIndividualSkeletonButton.setEnabled(False)

        self.generateSampleSkeletonsButton = QPushButton("Generate Skeletons for Current Sample")
        self.generateSampleSkeletonsButton.clicked.connect(self.GenerateSampleSkeletons)
        layout.addWidget(self.generateSampleSkeletonsButton)
        self.generateSampleSkeletonsButton.setEnabled(False)

        self.sliderMap = {}

        self.skeletonLayouts = {}

        self.mainImageLayout = QVBoxLayout()
        layout.addLayout(self.mainImageLayout)

        for currSkeletonKey in self.skeletonMap:
            currSkeletonLayout = QHBoxLayout()
            currLayout = QVBoxLayout()
            currSkeletonLayout.addLayout(currLayout)
            #layout.addLayout(currLayout)
            layout.addLayout(currSkeletonLayout)
            self.skeletonLayouts[currSkeletonKey] = currSkeletonLayout

            currLayout.addWidget(QLabel(f"{self.skeletonMap[currSkeletonKey]['name']}:"))
            
            currentResult = {}

            for parameterKey in self.skeletonMap[currSkeletonKey]["parameters"]:
                parameterInfo = self.skeletonMap[currSkeletonKey]["parameters"][parameterKey]

                currentSlider = SliderLineEditCombo(parameterInfo["name"], defaultVal=parameterInfo["default"], 
                                                    min_val=parameterInfo["min"], max_val=parameterInfo["max"], decimals=parameterInfo["decimals"])
                
                currentSlider.ValueChanged.connect(partial(self.TriggerParameterChanged, currSkeletonKey))

                currLayout.addLayout(currentSlider)

                currentResult[parameterKey] = currentSlider

            self.sliderMap[currSkeletonKey] = currentResult

    def TriggerParameterChanged(self, currSkeletonKey:str) -> None:
        self.ParametersChanged.emit(self.sliderMap, currSkeletonKey)

    def LoadOtherParameters(self, values:dict) -> None:
        for currSkeletonKey in self.sliderMap:
            for parameterKey in self.sliderMap[currSkeletonKey]:
                self.sliderMap[currSkeletonKey][parameterKey].UpdateValue(values[currSkeletonKey][parameterKey])

    def ReadDirectories(self) -> None:
        inputDir = self.inputDirLineEdit.text()
        outputDir = self.outputDirLineEdit.text()

        self.defaultInputDirectory = inputDir
        self.defaultOutputDirectory = outputDir
        self.CreateInitializationSettings()

        #create sample map based on input directory
        self.GetSamples(inputDir)

        if not os.path.exists(os.path.join(self.defaultOutputDirectory, "Calculations")):
            os.makedirs(os.path.join(self.defaultOutputDirectory, "Calculations"))

    def CreateSkeleton(self, fileName:str, sample:str) -> None:
        jsonResult = {}
        
        jsonResult[originalImageKey] = os.path.join(self.defaultInputDirectory, fileName)

        #save skeleton image file
        baseFileName, extension = os.path.splitext(fileName)
        
        #save JSON file for image
        fileNameSplit:list[str] = os.path.splitext(fileName)[0].split("_")
        timestamp = int(fileNameSplit[-1])

        jsonResult[timestampKey] = timestamp
        jsonResult[sampleKey] = sample
        
        #get result from skeleton creator
        for currSkeletonKey in self.skeletonMap:
            #create parameters
            parameters = {}
            for parameterKey in self.skeletonMap[currSkeletonKey]["parameters"]:
                parameters[parameterKey] = self.sliderMap[currSkeletonKey][parameterKey].value()

            skeletonResult = self.skeletonMap[currSkeletonKey]["function"](self.defaultInputDirectory, fileName,
                                                    parameters)

            newBaseFileName = baseFileName + "_" + currSkeletonKey
            newFileName = newBaseFileName + extension

            imgArray = skeletonResult[skeletonKey]
            img = Image.fromarray(np.asarray(imgArray * 255, dtype=np.uint8), mode="L")
            img = img.convert("RGB")
            img.save(os.path.join(self.defaultOutputDirectory, newFileName))

            skeletonResult[skeletonKey] = os.path.join(self.defaultOutputDirectory, newFileName)

            jsonResult[currSkeletonKey] = skeletonResult

        jsonFilePath = os.path.join(self.outputDirLineEdit.text(), "Calculations", baseFileName + "_calculations.json")
        jsonFile = open(jsonFilePath, "w")
        json.dump(jsonResult, jsonFile, indent=4)
        jsonFile.close()

    def GenerateSingleSkeleton(self) -> None:
        self.ReadDirectories()

        progressBar = ProgressBarPopup(maximum=2)
        progressBar.increment()
        progressBar.show()
        QApplication.processEvents()

        self.CreateSkeleton(self.currentFileList[self.currentIndex], self.currentSample)

        progressBar.increment()
        QApplication.processEvents()

        self.LoadImageIntoUI(self.currentIndex)

    def GenerateSampleSkeletons(self) -> None:
        self.ReadDirectories()

        progressBar = ProgressBarPopup(maximum=len(self.sampleToFiles[self.currentSample]))
        progressBar.show()
        QApplication.processEvents()

        for fileName in self.sampleToFiles[self.currentSample]:
            self.CreateSkeleton(fileName, self.currentSample)
            progressBar.increment()
            QApplication.processEvents()

        self.LoadImageIntoUI(self.currentIndex)

    def GenerateSkeletons(self) -> None:
        self.createdSkeletons = True
        
        self.ReadDirectories()

        totalFiles = 0
        for sample in self.sampleToFiles:
            totalFiles += len(self.sampleToFiles[sample])

        progressBar = ProgressBarPopup(maximum=totalFiles)
        progressBar.show()
        QApplication.processEvents()

        #loop through samples/files
        for sample in self.sampleToFiles:
            for fileName in self.sampleToFiles[sample]:
                self.CreateSkeleton(fileName, sample)
                progressBar.increment()
                QApplication.processEvents()

        #add skeleton UI
        self.AddSkeletonUI()

    def AddSkeletonUI(self) -> None:
        if self.skeletonUIAdded:
            self.LoadImageIntoUI(0)
            return
        
        self.skeletonUIAdded = True
        
        self.resize(1000, 500)

        self.generateIndividualSkeletonButton.setEnabled(True)
        self.generateSampleSkeletonsButton.setEnabled(True)

        mainImageAndInfoLayout = QHBoxLayout()
        self.mainImageLayout.addLayout(mainImageAndInfoLayout)

        infoLayout = QVBoxLayout()
        mainImageAndInfoLayout.addLayout(infoLayout)

        self.sampleDropdown = QComboBox()
        self.sampleDropdown.addItems(list(self.sampleToFiles.keys()))
        self.sampleDropdown.currentTextChanged.connect(self.LoadNewSample)
        self.sampleDropdown.setCurrentIndex(0)
        infoLayout.addWidget(self.sampleDropdown)

        self.timestampLabel = QLabel("Timestamp: N/A")
        self.timestampLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        infoLayout.addWidget(self.timestampLabel)

        self.originalImageLabel = ClickableLabel()
        self.originalImageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mainImageAndInfoLayout.addWidget(self.originalImageLabel)

        self.originalImageLabel.setPixmap(QPixmap(self.imageSize, self.imageSize))

        scrollButtonLayout = QHBoxLayout()
        self.mainImageLayout.addLayout(scrollButtonLayout)
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

        self.skeletonLabels = {}

        for currSkeletonKey in self.skeletonMap:
            skeletonLabel = ClickableLabel()
            skeletonLabel.clicked.connect(partial(self.GoIntoSkeletonView, currSkeletonKey))
            self.skeletonLabels[currSkeletonKey] = skeletonLabel

            currLayout = QVBoxLayout()
            self.skeletonLayouts[currSkeletonKey].addLayout(currLayout)

            currLayout.addWidget(skeletonLabel)

            skeletonLabel.setPixmap(QPixmap(self.imageSize, self.imageSize))

            buttonLayout = QHBoxLayout()
            currLayout.addLayout(buttonLayout)

            previewButton = QPushButton("Preview Steps")
            buttonLayout.addWidget(previewButton)

            previewButton.clicked.connect(partial(self.LoadPreview, currSkeletonKey))

            overlayButton = QPushButton("Toggle Overlay on Original")
            buttonLayout.addWidget(overlayButton)

            overlayButton.clicked.connect(partial(self.ToggleOverlay, currSkeletonKey))

        self.LoadNewSample(list(self.sampleToFiles.keys())[0])

    def GetCurrentCalculations(self) -> dict:
        imageFileName = self.currentFileList[self.currentIndex]

        #load calculation file
        calculationFileName = os.path.splitext(imageFileName)[0] + "_calculations.json"
        calculationFilePath = os.path.join(self.defaultOutputDirectory, "Calculations", calculationFileName)

        calculationFile = open(calculationFilePath, "r")
        calculations = json.load(calculationFile)
        calculationFile.close()

        return calculations

    def ToggleOverlay(self, currSkeletonKey:str) -> None:
        imageFileName = self.currentFileList[self.currentIndex]
        calculations = self.GetCurrentCalculations()
        
        if not currSkeletonKey in self.currentSkeletonsOverlayed:
            self.currentSkeletonsOverlayed.add(currSkeletonKey)
            
            originalImage = Image.open(os.path.join(self.defaultInputDirectory, imageFileName))
            originalImageArray = np.asarray(originalImage, dtype=np.float64).copy()

            maxValue = np.max(originalImageArray)
            minValue = np.min(originalImageArray)
            originalImageArray -= minValue
            maxValue -= minValue
            originalImageArray /= maxValue

            originalImagePixmap = ArrayToPixmap(originalImageArray, self.imageSize, False)

            overlayedPixmap = draw_lines_on_pixmap(calculations[currSkeletonKey][vectorKey][pointsKey], calculations[currSkeletonKey][vectorKey][linesKey], self.imageSize,
                                                   line_width=1, line_color=QColor("red"), pixmap=originalImagePixmap)

            self.skeletonLabels[currSkeletonKey].setPixmap(overlayedPixmap)

        else:
            self.currentSkeletonsOverlayed.remove(currSkeletonKey)

            skeletonPixmap = draw_lines_on_pixmap(calculations[currSkeletonKey][vectorKey][pointsKey], calculations[currSkeletonKey][vectorKey][linesKey], self.imageSize)

            self.skeletonLabels[currSkeletonKey].setPixmap(skeletonPixmap)

    def LoadPreview(self, currSkeletonKey:str) -> None:
        currImageName = self.currentFileList[self.currentIndex]

        currImagePath = os.path.join(self.defaultInputDirectory, currImageName)

        self.TriggerPreview.emit(currImagePath, currSkeletonKey)

    def LoadNewSample(self, value:str) -> None:
        self.currentFileList = self.sampleToFiles[value]

        self.currentSample = value

        self.LoadImageIntoUI(0)

    def GoIntoSkeletonView(self, currSkeletonKey:str) -> None:
        self.ClickedOnSkeleton.emit(self.currentFileList[self.currentIndex], currSkeletonKey)

    def LoadImageIntoUI(self, index:int) -> None:
        self.currentSkeletonsOverlayed = set()
        
        self.currentIndex = index

        imageFileName = self.currentFileList[index]

        calculations = self.GetCurrentCalculations()

        self.timestampLabel.setText(f"Timestamp: {calculations[timestampKey]}")

        originalImage = Image.open(os.path.join(self.defaultInputDirectory, imageFileName))
        originalImageArray = np.asarray(originalImage, dtype=np.float64).copy()

        maxValue = np.max(originalImageArray)
        minValue = np.min(originalImageArray)
        originalImageArray -= minValue
        maxValue -= minValue
        originalImageArray /= maxValue

        originalImagePixmap = ArrayToPixmap(originalImageArray, self.imageSize, False)

        self.originalImageLabel.setPixmap(originalImagePixmap)

        for currSkeletonKey in self.skeletonLabels:
            skeletonPixmap = draw_lines_on_pixmap(calculations[currSkeletonKey][vectorKey][pointsKey], calculations[currSkeletonKey][vectorKey][linesKey], self.imageSize)

            self.skeletonLabels[currSkeletonKey].setPixmap(skeletonPixmap)

        self.LoadedNewImage.emit(calculations)

    def SetParameterValues(self, values:dict) -> None:
        for currSkeletonKey in values:
            for parameterKey in values[currSkeletonKey]:
                self.sliderMap[currSkeletonKey][parameterKey].UpdateValue(values[currSkeletonKey][parameterKey])

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
        
        self.sampleToFiles = {}

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