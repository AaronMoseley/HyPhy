"""
Licensing Information:
Copyright 2025 Aaron Moseley

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files 
(the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, 
distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the 
following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
from PySide6.QtWidgets import QApplication, QWidget, QStackedLayout, QMainWindow
from PySide6.QtGui import QResizeEvent

from ImageOverview import ImageOverview
from SkeletonViewer import SkeletonViewer
from PreviewWindow import PreviewWindow
from ComparisonWindow import ComparisonWindow

from HelperFunctions import to_camel_case

import json
import os

class MainApplication(QWidget):
    def __init__(self) -> None:
        super().__init__()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_size = screen_geometry.size()

        # Set max size to screen size
        #self.setMaximumSize(screen_size)

        self.setFixedSize(screen_size.width(), screen_size.height() * 0.9)

        self.skeletonFileName = "SkeletonPipelines.json"
        self.stepsFileName = "PipelineSteps.json"
        self.parametersFileName = "StepParameters.json"
        self.parameterValuesFileName = "ParameterValues.json"

        skeletonFile = open(self.skeletonFileName, "r")
        self.skeletonPipelines = json.load(skeletonFile)
        skeletonFile.close()

        stepsFile = open(self.stepsFileName, "r")
        self.pipelineSteps = json.load(stepsFile)
        stepsFile.close()

        parametersFile = open(self.parametersFileName, "r")
        self.stepParameters = json.load(parametersFile)
        parametersFile.close()

        self.overview = ImageOverview(self.skeletonPipelines.copy(), self.pipelineSteps.copy(), self.stepParameters.copy())
        self.overview.ClickedOnSkeleton.connect(self.GoIntoViewer)
        self.overview.TriggerPreview.connect(self.GoIntoPreview)
        self.overview.ParametersChanged.connect(self.RetrieveParameterValues)
        self.overview.CompareToExternal.connect(self.GoIntoComparison)
        self.overview.SkeletonPipelineChanged.connect(self.SkeletonPipelineChanged)
        self.overview.SkeletonPipelineNameChanged.connect(self.SkeletonPipelineNameChanged)
        self.overview.PipelineAdded.connect(self.SkeletonPipelineAdded)
        self.overview.PipelineRemoved.connect(self.SkeletonPipelineRemoved)
        
        self.skeletonViewer = SkeletonViewer()
        self.skeletonViewer.BackButtonPressed.connect(self.BackToOverview)
        self.overview.LoadedNewImage.connect(self.skeletonViewer.SetCurrentImage)
        self.skeletonViewer.CommentsChanged.connect(self.overview.UpdateComments)

        self.previewWindow = PreviewWindow(self.skeletonPipelines.copy(), self.pipelineSteps.copy(), self.stepParameters.copy())
        self.previewWindow.BackToOverview.connect(self.BackToOverview)
        self.previewWindow.ParametersChanged.connect(self.RetrieveParameterValues)

        self.comparisonWindow = ComparisonWindow()
        self.comparisonWindow.BackToOverview.connect(self.BackToOverview)

        self.overview.LoadPreviousResults()

        self.primaryLayout = QStackedLayout(self)

        self.primaryLayout.addWidget(self.overview)
        self.primaryLayout.addWidget(self.skeletonViewer)
        self.primaryLayout.addWidget(self.previewWindow)
        self.primaryLayout.addWidget(self.comparisonWindow)
        self.primaryLayout.setCurrentWidget(self.overview)

        self.GetInitialParameterValues()

    def SkeletonPipelineChanged(self, newValues:dict) -> None:
        skeletonFile = open(self.skeletonFileName, "w")
        json.dump(newValues, skeletonFile, indent=4)
        skeletonFile.close()

        self.skeletonPipelines = newValues.copy()

        self.previewWindow.UpdateSkeletonPipelines(newValues.copy())

    def SkeletonPipelineAdded(self, newPipelineKey:str) -> None:
        self.parameterValues[newPipelineKey] = {}

    def SkeletonPipelineRemoved(self, currSkeletonKey:str) -> None:
        self.parameterValues.pop(currSkeletonKey)

    def SkeletonPipelineNameChanged(self, oldKey:str, newName:str) -> None:
        newKey = to_camel_case(newName)

        self.parameterValues[newKey] = self.parameterValues.pop(oldKey)

    def RetrieveParameterValues(self, values:list, currSkeletonKey:str) -> None:
        for i, stepName in enumerate(self.skeletonPipelines[currSkeletonKey]["steps"]):
            self.parameterValues[currSkeletonKey][f"{stepName}-{i}"] = values[i].copy()

        valuesFile = open(self.parameterValuesFileName, "w")
        json.dump(self.parameterValues, valuesFile, indent=4)
        valuesFile.close()

    def GetInitialParameterValues(self) -> None:
        if os.path.exists(self.parameterValuesFileName):
            valuesFile = open(self.parameterValuesFileName, "r")
            self.parameterValues = json.load(valuesFile)
            valuesFile.close()

            self.overview.SetParameterValues(self.parameterValues)
        else:
            self.parameterValues = {}
            for currSkeletonKey in self.skeletonPipelines:
                currEntry = {}

                for i, stepName in enumerate(self.skeletonPipelines[currSkeletonKey]["steps"]):
                    stepEntry = {}

                    for parameterName in self.pipelineSteps[stepName]["relatedParameters"]:
                        stepEntry[parameterName] = self.stepParameters[parameterName]["default"]

                    currEntry[f"{stepName}-{i}"] = stepEntry

                self.parameterValues[currSkeletonKey] = currEntry

            valuesFile = open(self.parameterValuesFileName, "w")
            json.dump(self.parameterValues, valuesFile, indent=4)
            valuesFile.close()

    def GoIntoPreview(self, currImagePath:str, currSkeletonKey:str) -> None:
        self.previewWindow.LoadNewImage(currImagePath, currSkeletonKey, self.parameterValues)
        self.primaryLayout.setCurrentWidget(self.previewWindow)

    def GoIntoViewer(self, imageName:str, currSkeletonKey:str) -> None:
        self.skeletonViewer.SetImage(imageName, currSkeletonKey)
        self.primaryLayout.setCurrentWidget(self.skeletonViewer)

    def GoIntoComparison(self, currSkeletonKey:str) -> None:
        self.comparisonWindow.SetImage(self.overview.GetCurrentCalculations(), currSkeletonKey)
        self.primaryLayout.setCurrentWidget(self.comparisonWindow)

    def BackToOverview(self) -> None:
        self.overview.SetParameterValues(self.parameterValues)
        self.primaryLayout.setCurrentWidget(self.overview)

    def resizeEvent(self, event:QResizeEvent):
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        if event.size().width() > screen_rect.width():
            event.size().setWidth(screen_rect.width())

        if event.size().height() > screen_rect.height():
            event.size().setHeight(screen_rect.height())

        return super().resizeEvent(event)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())