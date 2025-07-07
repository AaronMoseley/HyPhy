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

import json

class MainApplication(QWidget):
    def __init__(self) -> None:
        super().__init__()

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_size = screen_geometry.size()

        # Set max size to screen size
        #self.setMaximumSize(screen_size)

        self.setFixedSize(screen_size.width(), screen_size.height() * 0.9)

        skeletonFile = open("SkeletonMap.json", "r")
        self.skeletonMap = json.load(skeletonFile)
        skeletonFile.close()

        self.overview = ImageOverview(self.skeletonMap)
        self.overview.ClickedOnSkeleton.connect(self.GoIntoViewer)
        self.overview.TriggerPreview.connect(self.GoIntoPreview)
        self.overview.ParametersChanged.connect(self.RetrieveParameterValues)
        
        self.skeletonViewer = SkeletonViewer()
        self.skeletonViewer.BackButtonPressed.connect(self.BackToOverview)
        self.overview.LoadedNewImage.connect(self.skeletonViewer.SetCurrentImage)

        self.previewWindow = PreviewWindow(self.skeletonMap)
        self.previewWindow.BackToOverview.connect(self.BackToOverview)
        self.previewWindow.ParametersChanged.connect(self.RetrieveParameterValues)

        self.overview.LoadPreviousResults()

        #centralWidget = QWidget()
        self.primaryLayout = QStackedLayout(self)
        #self.setCentralWidget(centralWidget)    

        self.primaryLayout.addWidget(self.overview)
        self.primaryLayout.addWidget(self.skeletonViewer)
        self.primaryLayout.addWidget(self.previewWindow)
        self.primaryLayout.setCurrentWidget(self.overview)

        self.GetInitialParameterValues()

    def RetrieveParameterValues(self, sliderMap:dict, currSkeletonKey:str) -> None:
        for parameterKey in sliderMap[currSkeletonKey]:
            self.parameterValues[currSkeletonKey][parameterKey] = sliderMap[currSkeletonKey][parameterKey].value()

    def GetInitialParameterValues(self) -> None:
        self.parameterValues = {}
        for currSkeletonKey in self.skeletonMap:
            currEntry = {}

            for parameterKey in self.skeletonMap[currSkeletonKey]["parameters"]:
                currEntry[parameterKey] = self.skeletonMap[currSkeletonKey]["parameters"][parameterKey]["default"]

            self.parameterValues[currSkeletonKey] = currEntry

    def GoIntoPreview(self, currImagePath:str, currSkeletonKey:str) -> None:
        self.previewWindow.LoadNewImage(currImagePath, currSkeletonKey, self.parameterValues)
        self.primaryLayout.setCurrentWidget(self.previewWindow)

    def GoIntoViewer(self, imageName:str, currSkeletonKey:str) -> None:
        self.skeletonViewer.SetImage(imageName, currSkeletonKey)
        self.primaryLayout.setCurrentWidget(self.skeletonViewer)

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