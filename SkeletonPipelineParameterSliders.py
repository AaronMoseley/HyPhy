from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont

from SliderLineEditCombo import SliderLineEditCombo
from StepWithParameters import StepWithParameters
from HelperFunctions import to_camel_case

class SkeletonPipelineParameterSliders(QVBoxLayout):
    ValueChanged = Signal(str)
    #skeleton key, skeleton pipeline
    UpdatedSkeletonPipeline = Signal(str, dict)
    #old key, new name
    UpdatedSkeletonName = Signal(str, str)

    DeleteSkeletonPipeline = Signal(str)
    
    def __init__(self, currSkeletonKey:str, skeletonPipelines:dict, pipelineSteps:dict, parameters:dict, editable:bool) -> None:
        super().__init__()
        
        self.currSkeletonKey = currSkeletonKey
        self.skeletonPipelines = skeletonPipelines
        self.pipelineSteps = pipelineSteps
        self.parameters = parameters

        self.editable = editable

        self.currentlyUpdatingValues = False

        self.AddUI()

    def AddUI(self) -> None:
        #add label
        if self.editable:
            topLayout = QHBoxLayout()
            self.addLayout(topLayout)

            titleLabel = QLineEdit(self.skeletonPipelines[self.currSkeletonKey]["name"])
            titleLabel.textChanged.connect(self.TriggerSkeletonNameChanged)
            topLayout.addWidget(titleLabel, stretch=2)

            deleteButton = QPushButton("X")
            topLayout.addWidget(deleteButton, stretch=1)
            deleteButton.clicked.connect(self.TriggerDeletePipeline)
        else:
            titleLabel = QLabel(self.skeletonPipelines[self.currSkeletonKey]["name"])
            self.addWidget(titleLabel)

        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(18)
        titleFont.setUnderline(True)
        titleLabel.setFont(titleFont)

        self.stepObjects:dict[str, StepWithParameters] = {}

        stepNameFont = QFont()
        stepNameFont.setPointSize(12)

        self.stepLayout = QVBoxLayout()
        self.addLayout(self.stepLayout)

        #loop through steps
        for i, stepName in enumerate(self.skeletonPipelines[self.currSkeletonKey]["steps"]):
            step = StepWithParameters(
                self.skeletonPipelines,
                self.pipelineSteps,
                self.parameters,
                i,
                stepName,
                self.editable
            )

            if self.editable:
                step.DeleteStepPressed.connect(self.DeleteButtonPressed)
                step.StepNameChanged.connect(self.StepNameChanged)

                if i < len(self.skeletonPipelines[self.currSkeletonKey]["steps"]) - 1:
                    step.DeleteButtonSetEnabled(False)

            step.ValueChanged.connect(self.TriggerValueChanged)

            self.stepLayout.addLayout(step)

            self.stepObjects[f"{stepName}-{i}"] = step

        if self.editable:
            addStepButton = QPushButton("Add Step")
            addStepButton.clicked.connect(self.AddStep)
            self.addWidget(addStepButton)

        self.skeletonizeLabel = QLabel(f"{len(self.skeletonPipelines[self.currSkeletonKey]['steps']) + 1}. Skeletonize")
        self.skeletonizeLabel.setFont(stepNameFont)
        self.addWidget(self.skeletonizeLabel)

    def TriggerSkeletonNameChanged(self, newName:str) -> None:
        oldKey = self.currSkeletonKey
        newKey = to_camel_case(newName)
        self.currSkeletonKey = newKey

        self.skeletonPipelines[newKey] = self.skeletonPipelines.pop(oldKey)
        self.skeletonPipelines[newKey]["name"] = newName

        self.UpdatedSkeletonName.emit(oldKey, newName)

    def RemoveLayout(self, layout:QVBoxLayout|QHBoxLayout) -> None:
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)

            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self.RemoveLayout(item.layout())  # Recursively remove child layouts

            layout.removeItem(item)

        # Find and remove layout from parent layout
        for i in range(self.stepLayout.count()):
            item = self.stepLayout.itemAt(i)
            if item and item.layout() == layout:
                self.stepLayout.takeAt(i)
                break

        # Optionally delete the layout
        del layout

    def DeleteButtonPressed(self) -> None:
        stepIndex = len(self.stepObjects) - 1
        stepName = self.skeletonPipelines[self.currSkeletonKey]["steps"].pop()
        
        #remove step object layout
        self.RemoveLayout(self.stepObjects[f"{stepName}-{stepIndex}"])

        if f"{stepName}-{stepIndex}" in self.stepObjects:
            del self.stepObjects[f"{stepName}-{stepIndex}"]

        #go through other steps
        for stepNameWithIndex in self.stepObjects:
            index = int(stepNameWithIndex.rsplit("-", 1)[1])

            stepObject = self.stepObjects[stepNameWithIndex]

            #update delete button
            if index == len(self.stepObjects) - 1:
                stepObject.DeleteButtonSetEnabled(True)
            else:
                stepObject.DeleteButtonSetEnabled(False)
        
        self.skeletonizeLabel.setText(f"{len(self.skeletonPipelines[self.currSkeletonKey]['steps']) + 1}. Skeletonize")

        #emit changes to skeleton map
        self.UpdatedSkeletonPipeline.emit(self.currSkeletonKey, self.skeletonPipelines)

    def AddStep(self) -> None:
        #add new step object with first step in list
        stepIndex = len(self.stepObjects)
        stepName = list(self.pipelineSteps.keys())[0]

        newStepObject = StepWithParameters(
            self.skeletonPipelines,
            self.pipelineSteps,
            self.parameters,
            stepIndex,
            stepName,
            self.editable
        )

        newStepObject.ValueChanged.connect(self.TriggerValueChanged)

        self.stepLayout.addLayout(newStepObject)

        if self.editable:
            newStepObject.DeleteStepPressed.connect(self.DeleteButtonPressed)
            newStepObject.StepNameChanged.connect(self.StepNameChanged)

            #go through other steps
            for prevStepNameWithIndex in self.stepObjects:
                #update delete button
                self.stepObjects[prevStepNameWithIndex].DeleteButtonSetEnabled(False)
        
        self.stepObjects[f"{stepName}-{stepIndex}"] = newStepObject

        #emit changes to skeleton map
        self.skeletonPipelines[self.currSkeletonKey]["steps"].append(stepName)

        self.skeletonizeLabel.setText(f"{len(self.skeletonPipelines[self.currSkeletonKey]['steps']) + 1}. Skeletonize")

        self.UpdatedSkeletonPipeline.emit(self.currSkeletonKey, self.skeletonPipelines)

    def StepNameChanged(self, stepIndex:int, oldStepName:str, newStepName:str) -> None:
        #find correct step to switch based on index
        oldStepNameWithIndex = f"{oldStepName}-{stepIndex}"
        self.stepObjects[f"{newStepName}-{stepIndex}"] = self.stepObjects.pop(oldStepNameWithIndex)

        #switch step in skeleton pipeline
        self.skeletonPipelines[self.currSkeletonKey]["steps"][stepIndex] = newStepName

        #emit changes
        self.UpdatedSkeletonPipeline.emit(self.currSkeletonKey, self.skeletonPipelines)

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
        
        self.ValueChanged.emit(self.currSkeletonKey)

    def TriggerDeletePipeline(self) -> None:
        self.DeleteSkeletonPipeline.emit(self.currSkeletonKey)