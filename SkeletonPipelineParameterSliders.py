from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont

from SliderLineEditCombo import SliderLineEditCombo
from StepWithParameters import StepWithParameters

class SkeletonPipelineParameterSliders(QVBoxLayout):
    ValueChanged = Signal()
    
    def __init__(self, currSkeletonKey:str, skeletonPipelines:dict, pipelineSteps:dict, parameters:dict) -> None:
        super().__init__()
        
        self.currSkeletonKey = currSkeletonKey
        self.skeletonPipelines = skeletonPipelines
        self.pipelineSteps = pipelineSteps
        self.parameters = parameters

        self.currentlyUpdatingValues = False

        self.AddUI()

    def AddUI(self) -> None:
        #add label
        titleLabel = QLabel(self.skeletonPipelines[self.currSkeletonKey]["name"])

        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(14)
        titleLabel.setFont(titleFont)

        self.addWidget(titleLabel)

        self.stepObjects = {}

        stepNameFont = QFont()
        stepNameFont.setPointSize(12)

        #loop through steps
        for i, stepName in enumerate(self.skeletonPipelines[self.currSkeletonKey]["steps"]):
            step = StepWithParameters(
                self.skeletonPipelines,
                self.pipelineSteps,
                self.parameters,
                i,
                stepName
            )

            step.ValueChanged.connect(self.TriggerValueChanged)

            self.addLayout(step)

            self.stepObjects[f"{stepName}-{i}"] = step

    def GetValues(self) -> list:
        result = []

        #loop through each step
        for i, stepName in enumerate(self.skeletonPipelines[self.currSkeletonKey]["steps"]):
            currResult = self.stepObjects[f"{stepName}-{i}"].GetValues()

            result.append(currResult)
        
        return result
    
    def UpdateValues(self, values:dict) -> None:
        self.currentlyUpdatingValues = True

        for stepName in values:
            if stepName not in self.stepObjects:
                continue

            self.stepObjects[stepName].UpdateValues(values[stepName])

        self.currentlyUpdatingValues = False

    def TriggerValueChanged(self) -> None:
        if self.currentlyUpdatingValues:
            return
        
        self.ValueChanged.emit()