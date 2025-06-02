import sys
from PyQt6.QtWidgets import QApplication, QWidget, QStackedLayout, QMainWindow

from ImageOverview import ImageOverview


class MainApplication(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.overview = ImageOverview()

        centralWidget = QWidget()
        self.primaryLayout = QStackedLayout(centralWidget)
        self.setCentralWidget(centralWidget)    

        self.primaryLayout.addWidget(self.overview)
        self.primaryLayout.setCurrentWidget(self.overview)

# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec())