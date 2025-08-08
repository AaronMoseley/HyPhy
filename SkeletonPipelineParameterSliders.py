from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator

from .SliderLineEditCombo import SliderLineEditCombo

class SkeletonPipelineParameterSliders(QVBoxLayout):
    ValueChanged = Signal()
    
    def __init__(self, currSkeletonKey:str, skeletonPipelines:dict, pipelineSteps:dict, parameters:dict) -> None:
        super().__init__()
        
        self.currSkeletonKey = currSkeletonKey
        self.skeletonPipelines = skeletonPipelines
        self.pipelineSteps = pipelineSteps
        self.parameters = parameters

        self.AddUI()

    def AddUI(self) -> None:
        #add label
        self.addWidget(QLabel(self.skeletonPipelines[self.currSkeletonKey]["name"]))

        self.sliders = {}

        #loop through steps
        for i, stepName in enumerate(self.skeletonPipelines[self.currSkeletonKey]["steps"]):
            stepSliders = {}
            
            #add label for step
            self.addWidget(QLabel(f"{i}. {stepName}"))

            #loop through parameters
            for parameterName in self.pipelineSteps[stepName]["relatedParameters"]:
                #add slider/line edit for parameters
                currSlider = SliderLineEditCombo(
                    self.parameters[parameterName]["name"],
                    self.parameters[parameterName]["default"],
                    self.parameters[parameterName]["min"],
                    self.parameters[parameterName]["max"],
                    self.parameters[parameterName]["decimals"]
                )

                currSlider.ValueChanged.connect(self.ValueChanged.emit)

                self.addLayout(currSlider)

                stepSliders[parameterName] = currSlider

            self.sliders[f"{stepName}-{i}"] = stepSliders

    def GetValues(self) -> list:
        result = []

        #loop through each step
        for i, stepName in enumerate(self.skeletonPipelines[self.currSkeletonKey]["steps"]):
            currResult = {}
            
            #loop through parameter sliders for the step
            for parameterName in self.sliders[f"{stepName}-{i}"]:
                #append to resulting dict
                currResult[parameterName] = self.sliders[f"{stepName}-{i}"][parameterName].value()

            result.append(currResult)
        
        return result
    
    def UpdateValues(self, values:dict) -> None:
        for stepName in values:
            if stepName not in self.sliders:
                continue

            for parameterName in self.sliders[stepName]:
                self.sliders[stepName][parameterName].UpdateValue(values[stepName][parameterName])