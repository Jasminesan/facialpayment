from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from ui.ui_config import AppConfig

class SuccessView(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.finished.emit())
        self.init_ui()

    def showEvent(self, event):
        self.timer.start(3000)
        super().showEvent(event)

    def init_ui(self):
        # พื้นหลังขาว
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # ไอคอน
        self.lbl_icon = QLabel("✓")
        self.lbl_icon.setFixedSize(100, 100)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {AppConfig.COLOR_BTN_GREEN}; 
                color: white; 
                font-size: 60px; 
                border-radius: 50px;
            }}
        """)

        self.lbl_title = QLabel("Payment Approved")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 20px; background-color: transparent;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_subtitle = QLabel("Thank you.")
        self.lbl_subtitle.setStyleSheet("font-size: 14px; color: gray; background-color: transparent;")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)

    def set_user_name(self, name):
        self.lbl_subtitle.setText(f"Thank you. {name}")