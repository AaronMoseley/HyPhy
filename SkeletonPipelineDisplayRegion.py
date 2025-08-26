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

		skeletonLayout = QVBoxLayout()
		mainLayout.addLayout(skeletonLayout)

		self.sliders:dict[str, SkeletonPipelineParameterSliders] = {}
		self.skeletonLayouts:dict[str, QHBoxLayout] = {}
		self.skeletonDisplays:dict[str, SkeletonPipelineDisplay] = {}

		for currSkeletonKey in self.skeletonPipelines:
			self.skeletonLayouts[currSkeletonKey] = QHBoxLayout()
			mainLayout.addLayout(self.skeletonLayouts[currSkeletonKey])

			sliderLayout = SkeletonPipelineParameterSliders(
				currSkeletonKey, 
				self.skeletonPipelines.copy(), 
				self.pipelineSteps.copy(), 
				self.stepParameters.copy(), 
				True)
			self.skeletonLayouts[currSkeletonKey].addLayout(sliderLayout)

			sliderLayout.ValueChanged.connect(partial(self.TriggerParameterChanged, currSkeletonKey))
			sliderLayout.UpdatedSkeletonName.connect(self.TriggerSkeletonPipelineNameChanged)
			sliderLayout.UpdatedSkeletonPipeline.connect(self.TriggerSkeletonPipelineUpdated)
			self.sliders[currSkeletonKey] = sliderLayout

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