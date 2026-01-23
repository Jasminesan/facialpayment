from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap
import os
from ui.ui_config import AppConfig

class NoResultView(QWidget):
    retry_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.retry_clicked.emit())
        self.init_ui()

    def showEvent(self, event):
        self.timer.start(3000)
        super().showEvent(event)

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN};")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        lbl_title = QLabel("No Results Found")
        lbl_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {AppConfig.COLOR_TEXT_MAIN}; background-color: transparent;")

        lbl_img = QLabel()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(current_dir, "assets", "01.png") 
        
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_img.setPixmap(pixmap)
        else:
            lbl_img.setText("🐱")
            lbl_img.setStyleSheet("font-size: 50px;")

        layout.addWidget(lbl_title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_img, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)