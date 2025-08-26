from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel, QPushButton, QScrollArea, QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont, QPixmap

from ClickableLabel import ClickableLabel
from SliderLineEditCombo import SliderLineEditCombo
from StepWithParameters import StepWithParameters
from HelperFunctions import to_camel_case

from SkeletonPipelineDisplay import SkeletonPipelineDisplay
from SkeletonPipelineParameterSliders import SkeletonPipelineParameterSliders

from functools import partial

class SkeletonPipelineDisplayRegion(QScrollArea):
	ParameterChanged = Signal(str, list)
	SkeletonPipelineNameChanged = Signal(str, str)
	SkeletonPipelineModified = Signal(str, dict)

	GoIntoSkeletonView = Signal(str)
	LoadPreview = Signal(str)
	ToggleOverlay = Signal(str)
	CompareToExternalSkeleton = Signal(str)

	PipelineDeleted = Signal(str)
	PipelineAdded = Signal(str)
	
	def __init__(self, parent, skeletonPipelines:dict, pipelineSteps:dict, stepParameters:dict, imageSize:int) -> None:
		super().__init__(parent)

		self.setWidgetResizable(True)

		self.imageSize = imageSize

		self.skeletonPipelines = skeletonPipelines
		self.pipelineSteps = pipelineSteps
		self.stepParameters = stepParameters

		self.AddUI()

	def AddUI(self) -> None:
		scrollContentWidget = QWidget()
		self.setWidget(scrollContentWidget)
		mainLayout = QVBoxLayout(scrollContentWidget)

		self.skeletonLayout = QVBoxLayout()
		mainLayout.addLayout(self.skeletonLayout)

		self.sliders:dict[str, SkeletonPipelineParameterSliders] = {}
		self.skeletonLayouts:dict[str, QHBoxLayout] = {}
		self.skeletonDisplays:dict[str, SkeletonPipelineDisplay] = {}

		for currSkeletonKey in self.skeletonPipelines:
			self.skeletonLayouts[currSkeletonKey] = QHBoxLayout()
			self.skeletonLayout.addLayout(self.skeletonLayouts[currSkeletonKey])

			sliderLayout = SkeletonPipelineParameterSliders(
				currSkeletonKey, 
				self.skeletonPipelines.copy(), 
				self.pipelineSteps.copy(), 
				self.stepParameters.copy(), 
				True)
			self.skeletonLayouts[currSkeletonKey].addLayout(sliderLayout)

			sliderLayout.ValueChanged.connect(self.TriggerParameterChanged)
			sliderLayout.UpdatedSkeletonName.connect(self.TriggerSkeletonPipelineNameChanged)
			sliderLayout.UpdatedSkeletonPipeline.connect(self.TriggerSkeletonPipelineUpdated)
			sliderLayout.DeleteSkeletonPipeline.connect(self.DeleteSkeletonizationPipeline)
			self.sliders[currSkeletonKey] = sliderLayout

		addPipelineButton = QPushButton("Add Skeletonization Pipeline")
		mainLayout.addWidget(addPipelineButton)
		addPipelineButton.clicked.connect(self.AddSkeletonizationPipeline)

	def AddSkeletonDisplays(self) -> None:
		for currSkeletonKey in self.skeletonPipelines:
			self.skeletonDisplays[currSkeletonKey] = SkeletonPipelineDisplay(currSkeletonKey, self.imageSize)
			self.skeletonLayouts[currSkeletonKey].addLayout(self.skeletonDisplays[currSkeletonKey])

			self.skeletonDisplays[currSkeletonKey].GoIntoSkeletonView.connect(self.GoIntoSkeletonView.emit)
			self.skeletonDisplays[currSkeletonKey].LoadPreview.connect(self.LoadPreview.emit)
			self.skeletonDisplays[currSkeletonKey].ToggleOverlay.connect(self.ToggleOverlay.emit)
			self.skeletonDisplays[currSkeletonKey].CompareToExternalSkeleton.connect(self.CompareToExternalSkeleton.emit)

	def TriggerParameterChanged(self, currSkeletonKey:str) -> None:
		self.ParameterChanged.emit(currSkeletonKey, self.GetParameterValues(currSkeletonKey))

	def SetPixmap(self, currSkeletonKey:str, newPixmap:QPixmap) -> None:
		if currSkeletonKey not in self.skeletonDisplays:
			return
		
		self.skeletonDisplays[currSkeletonKey].SetPixmap(newPixmap)

	def GetParameterValues(self, currSkeletonKey:str) -> list:
		return self.sliders[currSkeletonKey].GetValues()
	
	def TriggerSkeletonPipelineNameChanged(self, oldKey:str, newName:str) -> None:
		newKey = to_camel_case(newName)
		
		self.sliders[newKey] = self.sliders.pop(oldKey)

		if oldKey in self.skeletonDisplays:
			self.skeletonDisplays[newKey] = self.skeletonDisplays.pop(oldKey)
			self.skeletonDisplays[newKey].SetNewSkeletonKey(newKey)

		self.skeletonPipelines[newKey] = self.skeletonPipelines.pop(oldKey)

		self.SkeletonPipelineNameChanged.emit(oldKey, newName)

	def TriggerSkeletonPipelineUpdated(self, currSkeletonKey:str, newValues:dict) -> None:
		self.skeletonPipelines[currSkeletonKey] = newValues[currSkeletonKey]
		
		self.SkeletonPipelineModified.emit(currSkeletonKey, newValues)
	
	def SetParameterValues(self, newValues:dict) -> None:
		for currSkeletonKey in self.sliders:
			self.sliders[currSkeletonKey].UpdateValues(newValues[currSkeletonKey])

	def AddSkeletonizationPipeline(self) -> None:
		index = 1
		newPipelineName = "New Skeletonization Pipeline " + str(index)
		newPipelineKey = to_camel_case(newPipelineName)

		while newPipelineName in self.skeletonPipelines:
			index += 1
			newPipelineName = "New Skeletonization Pipeline " + str(index)
			newPipelineKey = to_camel_case(newPipelineName)

		self.skeletonPipelines[newPipelineKey] = {
			"name": newPipelineName,
			"steps": []
		}

		self.skeletonLayouts[newPipelineKey] = QHBoxLayout()
		self.skeletonLayout.addLayout(self.skeletonLayouts[newPipelineKey])

		sliderLayout = SkeletonPipelineParameterSliders(
			newPipelineKey, 
			self.skeletonPipelines.copy(), 
			self.pipelineSteps.copy(), 
			self.stepParameters.copy(), 
			True)
		self.skeletonLayouts[newPipelineKey].addLayout(sliderLayout)

		sliderLayout.ValueChanged.connect(partial(self.TriggerParameterChanged, newPipelineKey))
		sliderLayout.UpdatedSkeletonName.connect(self.TriggerSkeletonPipelineNameChanged)
		sliderLayout.UpdatedSkeletonPipeline.connect(self.TriggerSkeletonPipelineUpdated)
		sliderLayout.DeleteSkeletonPipeline.connect(self.DeleteSkeletonizationPipeline)
		self.sliders[newPipelineKey] = sliderLayout

		self.skeletonDisplays[newPipelineKey] = SkeletonPipelineDisplay(newPipelineKey, self.imageSize)
		self.skeletonLayouts[newPipelineKey].addLayout(self.skeletonDisplays[newPipelineKey])

		self.skeletonDisplays[newPipelineKey].GoIntoSkeletonView.connect(self.GoIntoSkeletonView.emit)
		self.skeletonDisplays[newPipelineKey].LoadPreview.connect(self.LoadPreview.emit)
		self.skeletonDisplays[newPipelineKey].ToggleOverlay.connect(self.ToggleOverlay.emit)
		self.skeletonDisplays[newPipelineKey].CompareToExternalSkeleton.connect(self.CompareToExternalSkeleton.emit)

		self.PipelineAdded.emit(newPipelineName)

	def RemoveLayout(self, layout:QVBoxLayout|QHBoxLayout) -> None:
		for i in reversed(range(layout.count())):
			item = layout.itemAt(i)

			if item.widget():
				item.widget().setParent(None)
			elif item.layout():
				self.RemoveLayout(item.layout())  # Recursively remove child layouts

			layout.removeItem(item)

		# Find and remove layout from parent layout
		for i in range(self.skeletonLayout.count()):
			item = self.skeletonLayout.itemAt(i)
			if item and item.layout() == layout:
				self.skeletonLayout.takeAt(i)
				break

		# Optionally delete the layout
		del layout

	def DeleteSkeletonizationPipeline(self, currSkeletonKey:str) -> None:
		self.RemoveLayout(self.skeletonLayouts[currSkeletonKey])

		self.sliders.pop(currSkeletonKey)
		self.skeletonDisplays.pop(currSkeletonKey)
		self.skeletonLayouts.pop(currSkeletonKey)

		self.skeletonPipelines.pop(currSkeletonKey)

		self.PipelineDeleted.emit(currSkeletonKey)