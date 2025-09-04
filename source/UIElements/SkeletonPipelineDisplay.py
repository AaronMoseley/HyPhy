from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QSlider, QLineEdit, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont, QPixmap, QColor

from source.UIElements.ClickableLabel import ClickableLabel
from source.UIElements.SliderLineEditCombo import SliderLineEditCombo
from source.UIElements.StepWithParameters import StepWithParameters
from source.Helpers.HelperFunctions import to_camel_case

from functools import partial

class SkeletonPipelineDisplay(QVBoxLayout):
    GoIntoSkeletonView = Signal(str)
    LoadPreview = Signal(str)
    CompareToExternalSkeleton = Signal(str)
    ToggleOverlay = Signal(str)
    
    def __init__(self, currSkeletonKey:str, imageSize:int) -> None:
        super().__init__()

        self.skeletonKey = currSkeletonKey
        self.imageSize = imageSize

        self.AddUI()

    def AddUI(self) -> None:
        self.skeletonLabel = ClickableLabel()
        self.skeletonLabel.clicked.connect(self.TriggerSkeletonView)

        self.addWidget(self.skeletonLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        blackPixmap = QPixmap(self.imageSize, self.imageSize)
        blackPixmap.fill(QColor("black"))

        self.SetPixmap(blackPixmap)

        buttonLayout = QHBoxLayout()
        self.addLayout(buttonLayout)

        self.previewButton = QPushButton(" Preview Steps ")
        buttonLayout.addWidget(self.previewButton)

        self.previewButton.clicked.connect(self.TriggerLoadPreview)

        self.overlayButton = QPushButton(" Toggle Overlay on Original ")
        buttonLayout.addWidget(self.overlayButton)

        self.overlayButton.clicked.connect(self.TriggerToggleOverlay)

        self.comparisonButton = QPushButton(" Compare to External Skeleton ")
        buttonLayout.addWidget(self.comparisonButton)

        self.comparisonButton.clicked.connect(self.TriggerCompareToOtherSkeleton)

    def TriggerSkeletonView(self) -> None:
        self.GoIntoSkeletonView.emit(self.skeletonKey)

    def TriggerToggleOverlay(self) -> None:
        self.ToggleOverlay.emit(self.skeletonKey)

    def TriggerCompareToOtherSkeleton(self) -> None:
        self.CompareToExternalSkeleton.emit(self.skeletonKey)

    def TriggerLoadPreview(self) -> None:
        self.LoadPreview.emit(self.skeletonKey)

    def SetPixmap(self, newPixmap:QPixmap) -> None:
        self.skeletonLabel.setPixmap(newPixmap)

    def SetNewSkeletonKey(self, newSkeletonKey:str) -> None:
        self.skeletonKey = newSkeletonKey