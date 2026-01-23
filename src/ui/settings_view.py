from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
from ui.ui_config import AppConfig

class SettingsView(QWidget):
    back_clicked = Signal()
    language_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # พื้นหลังขาว
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # หัวข้อ Settings
        lbl_title = QLabel("Settings")
        lbl_title.setFont(QFont(AppConfig.FONT_FAMILY, 32, QFont.Weight.Bold))
        lbl_title.setStyleSheet("background-color: transparent;")
        layout.addWidget(lbl_title)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(line)

        layout.addSpacing(20)
        lbl_lang = QLabel("Languages")
        lbl_lang.setFont(QFont(AppConfig.FONT_FAMILY, 24))
        lbl_lang.setStyleSheet("background-color: transparent;")
        layout.addWidget(lbl_lang)

        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(30)
        lang_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.btn_eng = self.create_lang_btn("ENG", active=True)
        self.btn_eng.clicked.connect(lambda: self.set_language("ENG"))
        
        self.btn_tha = self.create_lang_btn("THA", active=False)
        self.btn_tha.clicked.connect(lambda: self.set_language("THA"))

        lang_layout.addWidget(self.btn_eng)
        lang_layout.addWidget(self.btn_tha)
        layout.addLayout(lang_layout)

        layout.addStretch()

        btn_back_layout = QHBoxLayout()
        btn_back_layout.addStretch()
        
        self.btn_back = QPushButton("BACK")
        self.btn_back.setFlat(True)
        self.btn_back.setFont(QFont(AppConfig.FONT_FAMILY, 20))
        self.btn_back.setStyleSheet(f"color: {AppConfig.COLOR_TEXT_MAIN}; text-align: right; background-color: transparent;")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        
        btn_back_layout.addWidget(self.btn_back)
        layout.addLayout(btn_back_layout)

    def create_lang_btn(self, text, active=False):
        btn = QPushButton(text)
        btn.setFixedSize(100, 50)
        btn.setFont(QFont(AppConfig.FONT_FAMILY, 18, QFont.Weight.Bold if active else QFont.Weight.Normal))
        self.update_btn_style(btn, active)
        return btn

    def update_btn_style(self, btn, active):
        if active:
            btn.setStyleSheet(f"color: {AppConfig.COLOR_BTN_GREEN}; border: 2px solid {AppConfig.COLOR_BTN_GREEN}; border-radius: 8px; background-color: #F1F8E9;")
        else:
            btn.setStyleSheet("color: #888888; border: none; background-color: transparent;")

    def set_language(self, lang):
        is_eng = (lang == "ENG")
        self.update_btn_style(self.btn_eng, is_eng)
        self.update_btn_style(self.btn_tha, not is_eng)
        self.language_changed.emit(lang)