import sys
from PySide6.QtWidgets import QApplication, QWidget, QStackedLayout, QMainWindow

from ImageOverview import ImageOverview
from SkeletonViewer import SkeletonViewer

class MainApplication(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.overview = ImageOverview()
        self.overview.ClickedOnSkeleton.connect(self.GoIntoViewer)
        
        self.skeletonViewer = SkeletonViewer()
        self.skeletonViewer.BackButtonPressed.connect(self.BackToOverview)
        self.overview.LoadedNewImage.connect(self.skeletonViewer.SetCurrentImage)

        self.overview.LoadPreviousResults()

        centralWidget = QWidget()
        self.primaryLayout = QStackedLayout(centralWidget)
        self.setCentralWidget(centralWidget)    

        self.primaryLayout.addWidget(self.overview)
        self.primaryLayout.addWidget(self.skeletonViewer)
        self.primaryLayout.setCurrentWidget(self.overview)

    def GoIntoViewer(self, imageName:str, currSkeletonKey:str) -> None:
        self.skeletonViewer.SetImage(imageName, currSkeletonKey)
        self.primaryLayout.setCurrentWidget(self.skeletonViewer)

    def BackToOverview(self) -> None:
        self.primaryLayout.setCurrentWidget(self.overview)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())