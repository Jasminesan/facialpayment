import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt, Signal
from ui.ui_config import AppConfig

class HomeView(QWidget):
    settings_clicked = Signal()
    start_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.bg_pixmap = None
        self.init_ui()

    def init_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "assets", "bg.jpg")
        
        if os.path.exists(image_path):
            self.bg_pixmap = QPixmap(image_path)
        else:
            self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        
        top_bar = QHBoxLayout()
        top_bar.addStretch() 
        
        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setStyleSheet("""
            QPushButton {
                color: #555; 
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: white;
            }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        top_bar.addWidget(self.btn_settings)
        
        layout.addLayout(top_bar)
        layout.addStretch()

    def paintEvent(self, event):
        if self.bg_pixmap:
            painter = QPainter(self)
            
            widget_w = self.width()
            widget_h = self.height()
            
            pixmap_w = self.bg_pixmap.width()
            pixmap_h = self.bg_pixmap.height()

            scale_w = widget_w / pixmap_w
            scale_h = widget_h / pixmap_h
            scale = max(scale_w, scale_h)

            new_w = int(pixmap_w * scale)
            new_h = int(pixmap_h * scale)

            x = (widget_w - new_w) // 2
            y = (widget_h - new_h) // 2

            scaled_pixmap = self.bg_pixmap.scaled(
                new_w, new_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(x, y, scaled_pixmap)

        super().paintEvent(event)

    def mousePressEvent(self, event):
        if not self.btn_settings.underMouse():
            self.start_clicked.emit()