from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel
from PyQt6.QtGui import QPixmap, QImage, QPen, QPainter, QColor
from PyQt6.QtCore import Qt, QPoint

import numpy as np

from functools import partial
from collections import OrderedDict

import os
import json
import cv2

from PIL import Image
import re

from CreateSkeleton import generate_skeletonized_images, skeletonKey, originalImageKey, statFunctionMap, vectorKey, pointsKey, linesKey

def camel_case_to_capitalized(text):
    """
    Converts a camel case string to a capitalized string with spaces.

    Args:
        text: The camel case string to convert.

    Returns:
        The capitalized string with spaces.
    """
    return re.sub(r"([A-Z])", r" \1", text).title()

class ImageOverview(QWidget):
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

        self.LoadPreviousResults()

    def NormalizeImageArray(self, array:np.ndarray) -> np.ndarray:
        arrayCopy = np.copy(array)
        
        maxValue = np.max(arrayCopy)
        minValue = np.min(arrayCopy)
        arrayCopy -= minValue
        maxValue -= minValue
        arrayCopy /= maxValue

        if arrayCopy.ndim > 2:
            return arrayCopy.mean(axis=-1)

        return arrayCopy
    
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
        self.skeletonLabel = QLabel()

        imageLayout.addWidget(self.originalImageLabel)
        imageLayout.addWidget(self.skeletonLabel)

        self.originalImageLabel.setPixmap(QPixmap(256, 256))
        self.skeletonLabel.setPixmap(QPixmap(256, 256))

        statsLayout = QVBoxLayout()
        middleSkeletonLayout.addLayout(statsLayout)

        self.calculationStatLabels = OrderedDict()

        for key in statFunctionMap:
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

    def LoadImageIntoUI(self, index:int) -> None:
        self.currentIndex = index

        imageFileName = list(self.currentResults.keys())[index]

        self.imageTitleLabel.setText(self.imageTitleLabelPrefix + imageFileName)

        originalImagePixmap = self.ArrayToPixmap(self.currentResults[imageFileName][originalImageKey], False, False)
        skeletonPixmap = self.draw_lines_on_pixmap(imageFileName)

        self.originalImageLabel.setPixmap(originalImagePixmap)
        self.skeletonLabel.setPixmap(skeletonPixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            self.calculationStatLabels[statsLabelKey].setText(f"{title}: {self.currentResults[imageFileName][statsLabelKey]}")

    def draw_lines_on_pixmap(self, imageName:str, width=249, height=249, line_color=QColor("white"), line_width=2):
        points = self.currentResults[imageName][vectorKey][pointsKey]
        lines = self.currentResults[imageName][vectorKey][linesKey]
        
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("black"))

        painter = QPainter(pixmap)
        pen = QPen(line_color)
        pen.setWidth(line_width)
        painter.setPen(pen)

        # Helper to scale normalized points to pixel coordinates
        def scale_point(p):
            x = int(p[0] * width)
            y = int((1 - p[1]) * height)
            return QPoint(x, y)

        for line in lines:
            if len(line) < 2:
                continue
            for i in range(len(line) - 1):
                p1 = scale_point(points[line[i]])
                p2 = scale_point(points[line[i + 1]])
                painter.drawLine(p1, p2)

        painter.end()
        return pixmap

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

    def ArrayToPixmap(self, array:np.ndarray, correctRange:bool=False, isSkeleton=False) -> QPixmap:
        arrayCopy = np.copy(array)
        
        if not correctRange:
            arrayCopy *= 255.0

        arrayCopy = np.asarray(arrayCopy, dtype=np.uint8)

        # Resize using OpenCV
        if not isSkeleton:
            resized_gray = cv2.resize(arrayCopy, (249, 249), interpolation=cv2.INTER_CUBIC)
        else:
            resized_gray = self.max_pool_downsample(arrayCopy, 249, 249)

        # Convert to RGB by stacking channels
        rgb_array = cv2.cvtColor(resized_gray, cv2.COLOR_GRAY2RGB)

        height, width, channels = rgb_array.shape
        bytesPerLine = width * channels
        qImage = QImage(rgb_array.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        qImage = qImage.copy()
        newPixmap = QPixmap.fromImage(qImage)
        return newPixmap

    def max_pool_downsample(self, binary_array, target_height, target_width):
        """
        Downsamples a 2D binary numpy array to the specified target size using max pooling.
        
        Parameters:
            binary_array (np.ndarray): 2D binary input array (values 0 or 1).
            target_height (int): Desired number of rows in output.
            target_width (int): Desired number of columns in output.
            
        Returns:
            np.ndarray: Downsampled binary array of shape (target_height, target_width).
        """
        
        h, w = binary_array.shape
        if h % target_height != 0 or w % target_width != 0:
            raise ValueError("Input dimensions must be divisible by target dimensions for exact pooling.")
        
        pool_h = h // target_height
        pool_w = w // target_width

        # Reshape and apply max pooling
        reshaped = binary_array.reshape(target_height, pool_h, target_width, pool_w)
        pooled = reshaped.max(axis=(1, 3))
        
        return pooled

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
            origImageArray = self.NormalizeImageArray(origImageArray)

            currEntry[originalImageKey] = origImageArray

            #load skeleton, normalize it to 0-1
            skeletonImage = Image.open(os.path.join(self.defaultOutputDirectory, skeletonFileName))
            skeletonArray = np.asarray(skeletonImage, dtype=np.float64)
            skeletonArray = self.NormalizeImageArray(skeletonArray)

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