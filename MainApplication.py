import sys
from PySide6.QtWidgets import QApplication, QWidget, QStackedLayout, QMainWindow

from ImageOverview import ImageOverview
from SkeletonViewer import SkeletonViewer
from PreviewWindow import PreviewWindow

from CreateSkeleton import GenerateMatureHyphageSkeleton, GenerateNetworkSkeleton, RadialThreshold, CallRemoveSmallWhiteIslands, CallRemoveStructurallyNoisyIslands, CallSmoothBinaryArray, CallSkeletonize, CallAdjustContrast, CallEdgeDetection

class MainApplication(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.skeletonMap = {
            "matureHyphage": {
                "name": "Mature Hyphage",
                "function": GenerateMatureHyphageSkeleton,
                "steps": [
                    {
                        "name": "Radial Threshold",
                        "relatedParameters": ["centerThreshold", "edgeThreshold"],
                        "function": RadialThreshold
                    },
                    {
                        "name": "Remove Small White Islands",
                        "relatedParameters": ["minWhiteIslandSize"],
                        "function": CallRemoveSmallWhiteIslands
                    },
                    {
                        "name": "Remove Noisy Islands",
                        "relatedParameters": ["noiseTolerance"],
                        "function": CallRemoveStructurallyNoisyIslands
                    },
                    {
                        "name": "Smooth Image",
                        "relatedParameters": ["gaussianBlurSigma"],
                        "function": CallSmoothBinaryArray
                    },
                    {
                        "name": "Skeletonize",
                        "relatedParameters": [],
                        "function": CallSkeletonize
                    }
                ],
                "parameters": {
                    "centerThreshold": {
                        "name": "Center Threshold",
                        "decimals": 3,
                        "min": 0.0,
                        "max": 1.0,
                        "default": 0.515
                    },
                    "edgeThreshold": {
                        "name": "Edge Threshold",
                        "decimals": 3,
                        "min": 0.0,
                        "max": 1.0,
                        "default": 0.12
                    },
                    "minWhiteIslandSize": {
                        "name": "Minimum Size for White Areas (pixels)",
                        "decimals": 0,
                        "min": 100,
                        "max": 1500,
                        "default": 800
                    },
                    "noiseTolerance": {
                        "name": "Noisy Island Tolerance",
                        "decimals": 2,
                        "min": 0.0,
                        "max": 4.0,
                        "default": 0.15
                    },
                    "gaussianBlurSigma": {
                        "name": "Gaussian Blur Sigma",
                        "decimals": 2,
                        "min": 0.0,
                        "max": 4.0,
                        "default": 1.2
                    }
                }
            },
            "network": {
                "name": "Fungal Network",
                "function": GenerateNetworkSkeleton,
                "steps": [
                    {
                        "name": "Adjust Contrast",
                        "relatedParameters": ["contrastAdjustment"],
                        "function": CallAdjustContrast
                    },
                    {
                        "name": "Edge Detection",
                        "relatedParameters": ["gaussianBlurSigma", "maxThreshold", "minThreshold", "edgeNeighborRatio"],
                        "function": CallEdgeDetection
                    },
                    {
                        "name": "Smooth Image",
                        "relatedParameters": ["gaussianBlurSigma"],
                        "function": CallSmoothBinaryArray
                    },
                    {
                        "name": "Remove Small White Islands",
                        "relatedParameters": ["minWhiteIslandSize"],
                        "function": CallRemoveSmallWhiteIslands
                    },
                    {
                        "name": "Skeletonize",
                        "relatedParameters": [],
                        "function": CallSkeletonize
                    }
                ],
                "parameters": {
                    "contrastAdjustment": {
                        "name": "Contrast Adjustment",
                        "decimals": 2,
                        "min": 1.0,
                        "max": 4.0,
                        "default": 2.0
                    },
                    "minThreshold": {
                        "name": "Minimum Bound",
                        "decimals": 3,
                        "min": 0.0,
                        "max": 1.0,
                        "default": 0.05
                    },
                    "maxThreshold": {
                        "name": "Maximum Bound",
                        "decimals": 3,
                        "min": 0.0,
                        "max": 1.0,
                        "default": 0.9
                    },
                    "edgeNeighborRatio": {
                        "name": "Minimum Edge Neighbor Ratio",
                        "decimals": 3,
                        "min": 0.0,
                        "max": 1.0,
                        "default": 0.1
                    },
                    "gaussianBlurSigma": {
                        "name": "Gaussian Blur Sigma",
                        "decimals": 2,
                        "min": 0.0,
                        "max": 4.0,
                        "default": 1.2
                    },
                    "minWhiteIslandSize": {
                        "name": "Minimum Size for White Areas (pixels)",
                        "decimals": 0,
                        "min": 0,
                        "max": 1000,
                        "default": 50
                    }
                }
            }
        }

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

        centralWidget = QWidget()
        self.primaryLayout = QStackedLayout(centralWidget)
        self.setCentralWidget(centralWidget)    

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

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())