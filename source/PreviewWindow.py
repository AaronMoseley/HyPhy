from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFileDialog, QLabel, QComboBox, QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

import numpy as np

from functools import partial

import os
import json

from PIL import Image

from source.Helpers.HelperFunctions import ArrayToPixmap, NormalizeImageArray

from source.UIElements.SkeletonPipelineParameterSliders import SkeletonPipelineParameterSliders

from source.Helpers.CreateSkeleton import stepFunctionMap

class PreviewWindow(QWidget):
	BackToOverview = Signal()
	ParametersChanged = Signal(list, str)

	def __init__(self, skeletonPipelines:dict, pipelineSteps:dict, stepParameters:dict):
		super().__init__()

		self.skeletonPipelines = skeletonPipelines
		self.pipelineSteps = pipelineSteps
		self.stepParameters = stepParameters

		self.imageResolution = 512

		self.currentStepIndex:int = 0
		self.currentSkeletonKey:str = ""

		self.originalImageArray:np.ndarray = None

		self.sliders = None

		self.CreateUI()

	def UpdateSkeletonPipelines(self, newValues:dict) -> None:
		self.skeletonPipelines = newValues

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

		self.parameterLayout = QVBoxLayout()
		leftLayout.addLayout(self.parameterLayout)

		#right VQBox, contains name of step, related parameters, original image pixmap, skeleton pixmap, right/left buttons
		rightLayout = QVBoxLayout()
		mainLayout.addLayout(rightLayout)

		self.imageNameLabel = QLabel("")
		rightLayout.addWidget(self.imageNameLabel)

		self.skeletonNameLabel = QLabel("")

		self.stepNameLabel = QLabel("")
		rightLayout.addWidget(self.stepNameLabel)

		self.relevantParametersLabel = QLabel("")
		rightLayout.addWidget(self.relevantParametersLabel)

		self.mainImageLabel = QLabel()
		mainImagePixmap = QPixmap(self.imageResolution, self.imageResolution)
		self.mainImageLabel.setPixmap(mainImagePixmap)
		rightLayout.addWidget(self.mainImageLabel)

		self.skeletonLabel = QLabel()
		skeletonPixmap = QPixmap(self.imageResolution, self.imageResolution)
		self.skeletonLabel.setPixmap(skeletonPixmap)
		rightLayout.addWidget(self.skeletonLabel)

		refreshButton = QPushButton("Refresh Step")
		rightLayout.addWidget(refreshButton)
		refreshButton.clicked.connect(self.LoadSkeletonStep)

		scrollButtonLayout = QHBoxLayout()
		rightLayout.addLayout(scrollButtonLayout)
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

	def ChangeIndex(self, direction:int) -> None:
		newIndex = self.currentStepIndex + direction

		if newIndex < 0:
			newIndex = 0

		if newIndex >= len(self.skeletonPipelines[self.currentSkeletonKey]["steps"]):
			newIndex = len(self.skeletonPipelines[self.currentSkeletonKey]["steps"]) - 1

		if newIndex == 0:
			self.rightButton.setEnabled(True)
			self.leftButton.setEnabled(False)
		elif newIndex == len(self.skeletonPipelines[self.currentSkeletonKey]["steps"]) - 1:
			self.rightButton.setEnabled(False)
			self.leftButton.setEnabled(True)
		else:
			self.rightButton.setEnabled(True)
			self.leftButton.setEnabled(True)

		if newIndex != self.currentStepIndex:
			self.currentStepIndex = newIndex
			self.LoadSkeletonStep()

	def LoadNewImage(self, imagePath:str, currSkeletonKey:str, parameterValues:dict) -> None:
		#load image name and create all the sliders
		
		imageName = os.path.splitext(os.path.basename(imagePath))[0]
		self.imageNameLabel.setText(f"Image: {imageName}")

		self.currentStepIndex = 0
		self.currentSkeletonKey = currSkeletonKey

		self.skeletonNameLabel.setText(f"Skeleton Type: {self.skeletonPipelines[self.currentSkeletonKey]['name']}")

		self.AddParameterSliders(parameterValues)

		origImg = Image.open(imagePath)
		self.originalImageArray = np.asarray(origImg, dtype=np.float64)
		self.originalImageArray = NormalizeImageArray(self.originalImageArray)
		origImgPixmap = ArrayToPixmap(self.originalImageArray, self.imageResolution)
		self.mainImageLabel.setPixmap(origImgPixmap)

		self.LoadSkeletonStep()

	def deleteItemsOfLayout(self, layout:(QVBoxLayout | QHBoxLayout)):
		if layout is not None:
			while layout.count():
				item = layout.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.setParent(None)
				else:
					self.deleteItemsOfLayout(item.layout())

	def TriggerParameterChanged(self, currSkeletonKey) -> None:
		parameters = self.sliders.GetValues()

		self.ParametersChanged.emit(parameters, currSkeletonKey)

	def AddParameterSliders(self, parameterValues:dict) -> None:
		self.deleteItemsOfLayout(self.parameterLayout)

		self.sliders = SkeletonPipelineParameterSliders(
			self.currentSkeletonKey, 
			self.skeletonPipelines.copy(), 
			self.pipelineSteps.copy(), 
			self.stepParameters.copy(), 
			False)
		self.sliders.ValueChanged.connect(self.TriggerParameterChanged)
		self.sliders.UpdateValues(parameterValues[self.currentSkeletonKey])
		self.parameterLayout.addLayout(self.sliders)

	def LoadSkeletonStep(self) -> None:
		currentStepName = self.skeletonPipelines[self.currentSkeletonKey]['steps'][self.currentStepIndex]

		#set step name label
		self.stepNameLabel.setText(f"Current Step: {currentStepName}")

		#set related parameters label
		relatedParametersText = "Related Parameters: "
		relatedParameters = []
		for parameterKey in self.pipelineSteps[currentStepName]["relatedParameters"]:
			relatedParameters.append(self.stepParameters[parameterKey]["name"])

		relatedParametersText += ", ".join(relatedParameters)

		self.relevantParametersLabel.setText(relatedParametersText)

		#create parameter dict
		parameters = self.sliders.GetValues()

		#calculate image
		skeletonArray = self.originalImageArray
		for i, stepName in enumerate(self.skeletonPipelines[self.currentSkeletonKey]["steps"][:self.currentStepIndex + 1]):
			stepFunctionKey = self.pipelineSteps[stepName]["function"]

			skeletonArray = stepFunctionMap[stepFunctionKey](skeletonArray, parameters[i])

		skeletonArray = np.asarray(skeletonArray, dtype=np.float64)

		skeletonPixmap = ArrayToPixmap(skeletonArray, self.imageResolution, maxPoolDownSample=True)
		self.skeletonLabel.setPixmap(skeletonPixmap)