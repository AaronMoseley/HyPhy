from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel, QPushButton, QComboBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont

from source.UIElements.SliderLineEditCombo import SliderLineEditCombo

class StepWithParameters(QHBoxLayout):
    ValueChanged = Signal()
    DeleteStepPressed = Signal()
    #step index, old step name, new step name
    StepNameChanged = Signal(int, str, str)
    
    def __init__(self, skeletonMap:dict, piplineSteps:dict, parameters:dict, stepIndex:int, stepName:str, editable:bool) -> None:
        super().__init__()
        
        self.skeletonMap = skeletonMap
        self.pipelineSteps = piplineSteps
        self.parameters = parameters
        self.stepIndex = stepIndex
        self.stepName = stepName

        self.editable = editable

        self.currentlyUpdatingValues = False

        self.AddUI()

    def AddUI(self) -> None:
        mainLayout = QVBoxLayout()
        self.addLayout(mainLayout)

        stepNameFont = QFont()
        stepNameFont.setPointSize(12)
        
        self.sliders = {}
            
        #add label for step
        if self.editable:
            stepLabelLayout = QHBoxLayout()
            mainLayout.addLayout(stepLabelLayout)

            stepIndexLabel = QLabel(f"{self.stepIndex + 1}.")
            stepIndexLabel.setFont(stepNameFont)
            stepLabelLayout.addWidget(stepIndexLabel, stretch=1, alignment=Qt.AlignmentFlag.AlignLeft)

            self.stepSelector = QComboBox()
            self.stepSelector.setFont(stepNameFont)
            #self.stepSelector.setCurrentText(self.stepName)
            self.stepSelector.addItems(list(self.pipelineSteps.keys()))

            index = list(self.pipelineSteps.keys()).index(self.stepName)
            self.stepSelector.setCurrentIndex(index)

            self.stepSelector.currentTextChanged.connect(self.TriggerStepNameChanged)
            stepLabelLayout.addWidget(self.stepSelector, stretch=10, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            self.stepNameLabel = QLabel(f"{self.stepIndex + 1}. {self.stepName}")
            self.stepNameLabel.setFont(stepNameFont)
            mainLayout.addWidget(self.stepNameLabel)

        self.sliderLayout = QVBoxLayout()
        mainLayout.addLayout(self.sliderLayout)

        self.AddStepSliders()

        if self.editable:
            self.deleteButton = QPushButton("X")
            self.deleteButton.clicked.connect(self.TriggerDelete)
            self.addWidget(self.deleteButton)

    def AddStepSliders(self) -> None:
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

            self.sliderLayout.addLayout(currSlider)

            self.sliders[parameterName] = currSlider

    def DeleteElementsOfLayout(self, layout:QVBoxLayout|QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    child_layout = item.layout()
                    if child_layout is not None:
                        self.DeleteElementsOfLayout(child_layout)

    def TriggerStepNameChanged(self, newStepName:str) -> None:
        #delete all sliders
        self.DeleteElementsOfLayout(self.sliderLayout)

        #add all new sliders for new step
        oldStepName = self.stepName
        self.stepName = newStepName
        self.AddStepSliders()

        #emit step name changed
        self.StepNameChanged.emit(self.stepIndex, oldStepName, newStepName)

    def TriggerDelete(self) -> None:
        self.DeleteStepPressed.emit()

    def DeleteButtonSetEnabled(self, state:bool) -> None:
        if not self.editable:
            return
        
        self.deleteButton.setEnabled(state)

    def SetIndex(self, newIndex:int) -> None:
        self.stepIndex = newIndex

        self.stepNameLabel.setText(f"{self.stepIndex + 1}. {self.stepName}")

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

    def ResetParameters(self) -> None:
        for parameterName in self.sliders:
            self.sliders[parameterName].UpdateValue(self.parameters[parameterName]["default"])