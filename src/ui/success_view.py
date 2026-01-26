from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QMovie 
import os 

from ui.ui_config import AppConfig

class SuccessView(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        
        self.movie = None 
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finished.emit)

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # ============================================================
        self.lbl_icon = QLabel()
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet("background-color: transparent;")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gif_path = os.path.join(current_dir, 'assets', 'check-correct.gif')

        if os.path.exists(gif_path):
            # โหลดไฟล์ GIF
            self.movie = QMovie(gif_path)
            self.movie.setCacheMode(QMovie.CacheMode.CacheAll) # ช่วยให้เล่นลื่นขึ้น
            
            self.movie.finished.connect(self.movie.stop)
            
            self.lbl_icon.setMovie(self.movie)
            self.movie.start()
        else:
            print(f"❌ Warning: GIF file not found at {gif_path}")
            self.lbl_icon.setText("✅")
            self.lbl_icon.setStyleSheet("font-size: 80px; background-color: transparent;")

        # ============================================================

        lbl_title = QLabel("PAYMENT SUCCESS")
        lbl_title.setStyleSheet(f"font-size: 30px; font-weight: bold; color: {AppConfig.COLOR_BTN_GREEN}; background-color: transparent;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_name = QLabel("User Name")
        self.lbl_name.setStyleSheet("font-size: 24px; font-weight: bold; background-color: transparent;")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_balance = QLabel("New Balance: 0.00") 
        self.lbl_balance.setStyleSheet("font-size: 20px; color: #888888; background-color: transparent;")
        self.lbl_balance.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(self.lbl_icon)
        layout.addWidget(lbl_title)
        layout.addSpacing(20)
        layout.addWidget(self.lbl_name)
        layout.addWidget(self.lbl_balance)
        layout.addStretch()

        self.setLayout(layout)

    def set_payment_details(self, name, new_balance):
        self.lbl_name.setText(name)
        self.lbl_balance.setText(f"ยอดคงเหลือ: {new_balance:,.2f} บาท")
        
        if self.movie:
            self.movie.jumpToFrame(0)
            self.movie.start()
            
        self.timer.start(2000)