from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
from ui.ui_config import AppConfig, t, get_lang

class SettingsView(QWidget):
    back_clicked = Signal()
    language_changed = Signal(str)
    pin_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 48, 64, 48)
        layout.setSpacing(18)

        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border: none;")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 30, 36, 30)
        card_layout.setSpacing(22)

        self.lbl_title = QLabel(t("settings.title_plain"))
        self.lbl_title.setFont(QFont(AppConfig.FONT_FAMILY, 30, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #111; background: transparent;")
        card_layout.addWidget(self.lbl_title)

        self.lang_container = QWidget()
        lang_v = QVBoxLayout(self.lang_container)
        lang_v.setContentsMargins(0, 0, 0, 0)
        lang_v.setSpacing(12)
        self.lbl_lang = QLabel(t("settings.language"))
        self.lbl_lang.setFont(QFont(AppConfig.FONT_FAMILY, 22))
        self.lbl_lang.setStyleSheet("color: #111; background-color: transparent;")
        lang_v.addWidget(self.lbl_lang)

        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(20)
        lang_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.btn_eng = self.create_lang_btn("ENG", active=(get_lang() == 'ENG'))
        self.btn_eng.clicked.connect(lambda: self.set_language("ENG"))
        
        self.btn_tha = self.create_lang_btn("THA", active=(get_lang() == 'THA'))
        self.btn_tha.clicked.connect(lambda: self.set_language("THA"))

        lang_layout.addWidget(self.btn_eng)
        lang_layout.addWidget(self.btn_tha)
        lang_v.addLayout(lang_layout)
        card_layout.addWidget(self.lang_container)

        card_layout.addStretch()

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(12)

        self.btn_pin = QPushButton(t("settings.pin"))
        self.btn_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pin.setMinimumHeight(52)
        self.btn_pin.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_pin.setFont(QFont(AppConfig.FONT_FAMILY, 24))
        self.btn_pin.setStyleSheet(
            """
            QPushButton {
                color: #111;
                background: transparent;
                border: none;
                text-align: left;
            }
            QPushButton:pressed { color: #444; }
            """
        )
        self.btn_pin.clicked.connect(self.pin_clicked.emit)
        bottom_row.addWidget(self.btn_pin)
        bottom_row.addStretch()

        self.btn_back = QPushButton(t("settings.back_plain"))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setMinimumHeight(52)
        self.btn_back.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.btn_back.setFont(QFont(AppConfig.FONT_FAMILY, 22))
        self.btn_back.setStyleSheet(
            """
            QPushButton {
                color: #111;
                background: transparent;
                border: none;
                text-align: right;
            }
            QPushButton:pressed { color: #444; }
            """
        )
        self.btn_back.clicked.connect(self.back_clicked.emit)
        bottom_row.addWidget(self.btn_back)
        card_layout.addLayout(bottom_row)

        layout.addWidget(card, 1)
        layout.addStretch()

    def update_language(self):
        self.lbl_title.setText(t("settings.title_plain"))
        self.lbl_lang.setText(t("settings.language"))
        self.btn_pin.setText(t("settings.pin"))
        self.btn_back.setText(t("settings.back_plain"))

    def create_lang_btn(self, text, active=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumSize(120, 56)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn.setFont(QFont(AppConfig.FONT_FAMILY, 18, QFont.Weight.Bold if active else QFont.Weight.Normal))
        self.update_btn_style(btn, active)
        return btn

    def update_btn_style(self, btn, active):
        if active:
            btn.setStyleSheet(
                """
                QPushButton {
                    color: white;
                    border: none;
                    border-radius: 8px;
                    background-color: #6B6B6B;
                }
                """
            )
        else:
            btn.setStyleSheet(
                """
                QPushButton {
                    color: #111;
                    border: none;
                    border-radius: 8px;
                    background-color: transparent;
                }
                """
            )

    def set_language(self, lang):
        is_eng = (lang == "ENG")
        self.update_btn_style(self.btn_eng, is_eng)
        self.update_btn_style(self.btn_tha, not is_eng)
        self.language_changed.emit(lang)