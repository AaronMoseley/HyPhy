from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont

from SliderLineEditCombo import SliderLineEditCombo

class StepWithParameters(QVBoxLayout):
    ValueChanged = Signal()
    
    def __init__(self, skeletonMap:dict, piplineSteps:dict, parameters:dict, stepIndex:int, stepName:str) -> None:
        super().__init__()
        
        self.skeletonMap = skeletonMap
        self.pipelineSteps = piplineSteps
        self.parameters = parameters
        self.stepIndex = stepIndex
        self.stepName = stepName

        self.currentlyUpdatingValues = False

        self.AddUI()

    def AddUI(self) -> None:
        stepNameFont = QFont()
        stepNameFont.setPointSize(12)
        
        self.sliders = {}
            
        #add label for step
        stepNameLabel = QLabel(f"{self.stepIndex + 1}. {self.stepName}")
        stepNameLabel.setFont(stepNameFont)
        self.addWidget(stepNameLabel)

        #loop through parameters
        for parameterName in self.pipelineSteps[self.stepName]["relatedParameters"]:
            #add slider/line edit for parameters
            currSlider = SliderLineEditCombo(
                "\t" + self.parameters[parameterName]["name"],
                self.parameters[parameterName]["default"],
                self.parameters[parameterName]["min"],
                self.parameters[parameterName]["max"],
                self.parameters[parameterName]["decimals"]
            )

            currSlider.ValueChanged.connect(self.TriggerValueChanged)

            self.addLayout(currSlider)

            self.sliders[parameterName] = currSlider

    def GetValues(self) -> list:
        result = {}
            
        #loop through parameter sliders for the step
        for parameterName in self.sliders:
            #append to resulting dict
            result[parameterName] = self.sliders[parameterName].value()
        
        return result
    
    def UpdateValues(self, values:dict) -> None:
        self.currentlyUpdatingValues = True

        for parameterName in self.sliders:
            self.sliders[parameterName].UpdateValue(values[parameterName])

        self.currentlyUpdatingValues = False

    def TriggerValueChanged(self) -> None:
        if self.currentlyUpdatingValues:
            return
        
        self.ValueChanged.emit()