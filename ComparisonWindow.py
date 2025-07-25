from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, QComboBox, QApplication
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, Signal

import numpy as np

from functools import partial

import os
import json

from PIL import Image

from HelperFunctions import draw_lines_on_pixmap, ArrayToPixmap, skeletonKey, originalImageKey, vectorKey, pointsKey, linesKey, timestampKey, sampleKey, NormalizeImageArray, comparisonFunctionMap, camel_case_to_capitalized
from ClickableLabel import ClickableLabel
from SliderLineEditCombo import SliderLineEditCombo
from ProgressBar import ProgressBarPopup

from CreateSkeleton import CallSkeletonize, VectorizeSkeleton

class ComparisonWindow(QWidget):
	BackToOverview = Signal()

	def __init__(self) -> None:
		super().__init__()

		self.imageResolution = 512

		self.comparisonStatsLabels:dict[str, QLabel] = {}

		self.skeletonType = None
		self.currentResults = None

		self.uploadedLines = None
		self.uploadedPoints = None

		self.currentlyOverlaying = False

		self.uploadedFile = False

		self.AddUI()

	def AddUI(self) -> None:
		mainLayout = QVBoxLayout()
		self.setLayout(mainLayout)
		
		topRowLayout = QHBoxLayout()
		mainLayout.addLayout(topRowLayout, 1)

		#back button
		backButton = QPushButton("Back")
		topRowLayout.addWidget(backButton, alignment=Qt.AlignmentFlag.AlignLeft)
		backButton.clicked.connect(self.CallBackToOverview)

		self.originalImageTextLabel = QLabel("Original Image: N/A")
		topRowLayout.addWidget(self.originalImageTextLabel, alignment=Qt.AlignmentFlag.AlignHCenter)

		imageLayout = QHBoxLayout()
		mainLayout.addLayout(imageLayout, 6)

		blackPixmap = QPixmap(self.imageResolution, self.imageResolution)
		blackPixmap.fill("black")

		#input image
		inputImageLayout = QVBoxLayout()
		imageLayout.addLayout(inputImageLayout)
		inputImageLayout.addWidget(QLabel("Input Image:"), 1)

		self.inputImageLabel = QLabel()
		self.inputImageLabel.setPixmap(blackPixmap)
		inputImageLayout.addWidget(self.inputImageLabel, 5, alignment=Qt.AlignmentFlag.AlignTop)

		#generated skeleton
		generatedImageLayout = QVBoxLayout()
		imageLayout.addLayout(generatedImageLayout)
		generatedImageLayout.addWidget(QLabel("Generated Skeleton:"), 1)

		self.generatedImageLabel = QLabel()
		self.generatedImageLabel.setPixmap(blackPixmap)
		generatedImageLayout.addWidget(self.generatedImageLabel, 5, alignment=Qt.AlignmentFlag.AlignTop)

		#uploaded skeleton
		uploadedImageLayout = QVBoxLayout()
		imageLayout.addLayout(uploadedImageLayout)
		uploadedImageLayout.addWidget(QLabel("Uploaded Skeleton:"), 1)

		self.uploadedImageLabel = QLabel()
		self.uploadedImageLabel.setPixmap(blackPixmap)
		uploadedImageLayout.addWidget(self.uploadedImageLabel, 5, alignment=Qt.AlignmentFlag.AlignTop)

		fileSelectorLayout = QHBoxLayout()
		uploadedImageLayout.addLayout(fileSelectorLayout)
		fileSelectButton = QPushButton("Upload File:")
		fileSelectButton.clicked.connect(self.UploadImage)
		fileSelectorLayout.addWidget(fileSelectButton)
		self.fileSelectLabel = QLabel("N/A")
		fileSelectorLayout.addWidget(self.fileSelectLabel)

		overlaySkeletonsButton = QPushButton("Toggle Generated Skeleton Overlay")
		overlaySkeletonsButton.clicked.connect(self.ToggleOverlay)
		uploadedImageLayout.addWidget(overlaySkeletonsButton)
		uploadedImageLayout.addWidget(QLabel("Note: Generated skeleton is blue, external skeleton is green"))

		#stats comparing the two
		statsLayout = QVBoxLayout()
		imageLayout.addLayout(statsLayout)

		for comparisonStatsKey in comparisonFunctionMap:
			currentLabel = QLabel(camel_case_to_capitalized(comparisonStatsKey) + ": N/A")
			statsLayout.addWidget(currentLabel)
			self.comparisonStatsLabels[comparisonStatsKey] = currentLabel

	def SetImage(self, currentResults:dict, currSkeletonKey:str) -> None:
		self.currentResults = currentResults
		self.skeletonType = currSkeletonKey

		#upload input image
		inputImagePath = currentResults["originalImage"]
		inputImageArray = np.asarray(Image.open(inputImagePath), dtype=np.float64)
		inputImageArray = NormalizeImageArray(inputImageArray)
		inputImagePixmap = ArrayToPixmap(inputImageArray, dimension=self.imageResolution)
		self.inputImageLabel.setPixmap(inputImagePixmap)

		#upload generated skeleton, draw vectorized version
		generatedSkeletonPixmap = draw_lines_on_pixmap(currentResults[currSkeletonKey][vectorKey][pointsKey], 
													   currentResults[currSkeletonKey][vectorKey][linesKey],
													   dimension=self.imageResolution)
		self.generatedImageLabel.setPixmap(generatedSkeletonPixmap)

		originalImageBaseName = os.path.basename(currentResults[originalImageKey])
		self.originalImageTextLabel.setText(f"Original Image: {originalImageBaseName}")

	def UploadImage(self) -> None:
		filePath = QFileDialog.getOpenFileName(self, "Select File")

		if not filePath:
			return
		
		if len(filePath) == 0:
			return
		
		if isinstance(filePath, tuple) or isinstance(filePath, list):
			filePath = filePath[0]
		
		filePath = filePath.replace("\\", "/")
		self.fileSelectLabel.setText(filePath)

		uploadedImageArray = np.asarray(Image.open(filePath), dtype=np.float64)
		uploadedImageArray = NormalizeImageArray(uploadedImageArray)

		uploadedSkeleton = CallSkeletonize(uploadedImageArray, {})
		self.uploadedLines, self.uploadedPoints, _ = VectorizeSkeleton(uploadedSkeleton)

		uploadedPixmap = draw_lines_on_pixmap(self.uploadedPoints, self.uploadedLines, dimension=self.imageResolution)
		self.uploadedImageLabel.setPixmap(uploadedPixmap)

		#perform calculations
		for comparisonStatKey in self.comparisonStatsLabels:
			result = comparisonFunctionMap[comparisonStatKey](
				(self.currentResults[self.skeletonType][vectorKey][linesKey], self.currentResults[self.skeletonType][vectorKey][pointsKey]),
				(self.uploadedLines, self.uploadedPoints)
			)

			self.comparisonStatsLabels[comparisonStatKey].setText(f"{camel_case_to_capitalized(comparisonStatKey)}: {result}")

		self.uploadedFile = True

	def ToggleOverlay(self) -> None:
		if not self.uploadedFile:
			return

		self.currentlyOverlaying = not self.currentlyOverlaying

		if not self.currentlyOverlaying:
			uploadedPixmap = draw_lines_on_pixmap(self.uploadedPoints, self.uploadedLines, dimension=self.imageResolution)
			self.uploadedImageLabel.setPixmap(uploadedPixmap)
		else:
			uploadedPixmap = draw_lines_on_pixmap(self.uploadedPoints, self.uploadedLines, dimension=self.imageResolution, line_color=QColor("green"))
			uploadedPixmap = draw_lines_on_pixmap(self.currentResults[self.skeletonType][vectorKey][pointsKey], 
												self.currentResults[self.skeletonType][vectorKey][linesKey],
												dimension=self.imageResolution, line_color=QColor("blue"), pixmap=uploadedPixmap)
			
			self.uploadedImageLabel.setPixmap(uploadedPixmap)

	def CallBackToOverview(self) -> None:
		self.uploadedFile = False
		self.fileSelectLabel.setText("N/A")
		uploadedImagePixmap = QPixmap(self.imageResolution, self.imageResolution)
		uploadedImagePixmap.fill("black")
		self.uploadedImageLabel.setPixmap(uploadedImagePixmap)
		self.originalImageTextLabel.setText("Original Image: N/A")

		self.skeletonType = None
		self.currentResults = None

		self.uploadedLines = None
		self.uploadedPoints = None

		self.currentlyOverlaying = False

		self.BackToOverview.emit()