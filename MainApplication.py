import sys
import os
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from functools import partial
from PIL import Image
from collections import OrderedDict
import cv2
import json

from CreateSkeleton import generate_skeletonized_images, skeletonKey, originalImageKey
import re

def camel_case_to_capitalized(text):
    """
    Converts a camel case string to a capitalized string with spaces.

    Args:
        text: The camel case string to convert.

    Returns:
        The capitalized string with spaces.
    """
    return re.sub(r"([A-Z])", r" \1", text).title()

class MainApplication(QWidget):
    def __init__(self):
        super().__init__()

        self.currentResults = OrderedDict()
        self.currentIndex = 0

        self.imageTitleLabelPrefix = "File Name: "

        self.workingDirectory = os.getcwd()

        self.createdSkeletons = False

        self.CreateUI()

    def CreateUI(self):
        # Set window title and size
        self.setWindowTitle("Fungal Structure Detector")
        self.setGeometry(100, 100, 500, 200)

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
        self.inputDirLineEdit.setText(os.path.join(self.workingDirectory, "Images"))
        inputDirLayout.addWidget(self.inputDirLineEdit)

        inputDirLabel.clicked.connect(partial(self.SelectDirectoryAndSetLineEdit, self.inputDirLineEdit))

        outputDirLayout = QHBoxLayout()
        layout.addLayout(outputDirLayout)
        outputDirLabel = QPushButton("Output Directory:")
        outputDirLayout.addWidget(outputDirLabel)
        self.outputDirLineEdit = QLineEdit()
        self.outputDirLineEdit.setPlaceholderText("...")
        self.outputDirLineEdit.setText(os.path.join(self.workingDirectory, "Skeletons"))
        outputDirLayout.addWidget(self.outputDirLineEdit)

        outputDirLabel.clicked.connect(partial(self.SelectDirectoryAndSetLineEdit, self.outputDirLineEdit))

        generateSkeletonsButton = QPushButton("Generate Skeletons")
        generateSkeletonsButton.clicked.connect(self.GenerateSkeletons)
        layout.addWidget(generateSkeletonsButton)

    def GenerateSkeletons(self) -> None:
        self.createdSkeletons = True
        
        inputDir = self.inputDirLineEdit.text()
        outputDir = self.outputDirLineEdit.text()

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

        jsonFilePath = os.path.join(self.outputDirLineEdit.text(), "calculations.json")
        jsonFile = open(jsonFilePath, "w")
        json.dump(jsonFileResult, jsonFile, indent=4)
        jsonFile.close()

        self.AddSkeletonUI(result)

    def AddSkeletonUI(self, skeletonResults:OrderedDict) -> None:
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

        firstFile = list(skeletonResults.keys())[0]
        for key in skeletonResults[firstFile]:
            if key == skeletonKey or key == originalImageKey:
                continue

            title = camel_case_to_capitalized(key)
            newLabel = QLabel(f"{title}: ")
            self.calculationStatLabels[key] = newLabel
            newLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            statsLayout.addWidget(newLabel)

        scrollButtonLayout = QHBoxLayout()
        skeletonLayout.addLayout(scrollButtonLayout)
        leftButton = QPushButton("🠨")
        font = leftButton.font()
        font.setPointSize(25)
        leftButton.setFont(font)
        scrollButtonLayout.addWidget(leftButton)
        leftButton.clicked.connect(partial(self.ChangeIndex, -1))

        rightButton = QPushButton("🠪")
        font = rightButton.font()
        font.setPointSize(25)
        rightButton.setFont(font)
        scrollButtonLayout.addWidget(rightButton)
        rightButton.clicked.connect(partial(self.ChangeIndex, 1))

        self.LoadImageIntoUI(0)

    def LoadImageIntoUI(self, index:int) -> None:
        self.currentIndex = index

        imageFileName = list(self.currentResults.keys())[index]

        self.imageTitleLabel.setText(self.imageTitleLabelPrefix + imageFileName)

        originalImagePixmap = self.ArrayToPixmap(self.currentResults[imageFileName][originalImageKey], False, False)
        skeletonPixmap = self.ArrayToPixmap(self.currentResults[imageFileName][skeletonKey], False, True)

        self.originalImageLabel.setPixmap(originalImagePixmap)
        self.skeletonLabel.setPixmap(skeletonPixmap)

        for statsLabelKey in self.calculationStatLabels:
            title = camel_case_to_capitalized(statsLabelKey)

            self.calculationStatLabels[statsLabelKey].setText(f"{title}: {self.currentResults[imageFileName][statsLabelKey]}")

    def ChangeIndex(self, direction:int) -> None:
        if self.currentIndex + direction < 0 or self.currentIndex + direction >= len(self.currentResults):
            return
        
        self.LoadImageIntoUI(self.currentIndex + direction)

    def ArrayToPixmap(self, array:np.ndarray, correctRange:bool=False, isSkeleton=False) -> QPixmap:
        arrayCopy = np.copy(array)
        
        if not correctRange:
            arrayCopy *= 255.0

        arrayCopy = np.asarray(arrayCopy, dtype=np.uint8)

        # Resize using OpenCV
        if not isSkeleton:
            resized_gray = cv2.resize(arrayCopy, (256, 256), interpolation=cv2.INTER_CUBIC)
        else:
            resized_gray = self.max_pool_downsample(arrayCopy, 256, 256)

        # Convert to RGB by stacking channels
        rgb_array = cv2.cvtColor(resized_gray, cv2.COLOR_GRAY2RGB)

        height, width, channels = rgb_array.shape
        bytesPerLine = width * channels
        qImage = QImage(rgb_array.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)
        qImage = qImage.copy()
        newPixmap = QPixmap.fromImage(qImage)
        return newPixmap

    def max_pool_downsample(self, image: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
        # Compute scale factors
        scale_y = image.shape[0] // target_height
        scale_x = image.shape[1] // target_width

        # Crop the image to make it divisible
        new_height = scale_y * target_height
        new_width = scale_x * target_width
        image_cropped = image[:new_height, :new_width]

        # Reshape and max-pool
        reshaped = image_cropped.reshape(target_height, scale_y, target_width, scale_x)
        pooled = reshaped.max(axis=(1, 3))

        return pooled.astype(np.uint8)

    def SelectDirectoryAndSetLineEdit(self, lineEdit:QLineEdit) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")

        if directory:
            lineEdit.setText(directory)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())