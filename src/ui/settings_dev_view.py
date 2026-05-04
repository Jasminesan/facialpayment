from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal

from ui.ui_config import AppConfig, t

class SettingsDevView(QWidget):
    register_clicked = Signal()
    topup_clicked = Signal()
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #FFFFFF;")

        root = QVBoxLayout(self)
        root.setContentsMargins(56, 44, 56, 44)
        root.setSpacing(16)

        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border: none;")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(24)

        self.lbl_title = QLabel(t("settings_dev.title"))
        self.lbl_title.setFont(QFont(AppConfig.FONT_FAMILY, 30, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #111;")
        lay.addWidget(self.lbl_title)

        self.btn_register = QPushButton(t("settings_dev.register"))
        self.btn_register.setMinimumHeight(96)
        self.btn_register.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_register.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register.setFont(QFont(AppConfig.FONT_FAMILY, 36, QFont.Weight.Medium))
        self.btn_register.setStyleSheet(
            """
            QPushButton {
                color: white;
                border: none;
                border-radius: 8px;
                background-color: #F17E82;
            }
            QPushButton:pressed { background-color: #E26E72; }
            """
        )
        self.btn_register.clicked.connect(self.register_clicked.emit)
        lay.addWidget(self.btn_register)

        self.btn_topup = QPushButton(t("settings_dev.topup"))
        self.btn_topup.setMinimumHeight(96)
        self.btn_topup.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_topup.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_topup.setFont(QFont(AppConfig.FONT_FAMILY, 36, QFont.Weight.Medium))
        self.btn_topup.setStyleSheet(
            """
            QPushButton {
                color: white;
                border: none;
                border-radius: 8px;
                background-color: #ABC57A;
            }
            QPushButton:pressed { background-color: #99B267; }
            """
        )
        self.btn_topup.clicked.connect(self.topup_clicked.emit)
        lay.addWidget(self.btn_topup)

        lay.addStretch()

        footer = QHBoxLayout()
        footer.addStretch()
        self.btn_back = QPushButton(t("settings_dev.back"))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setMinimumHeight(52)
        self.btn_back.setMinimumWidth(140)
        self.btn_back.setFont(QFont(AppConfig.FONT_FAMILY, 22))
        self.btn_back.setStyleSheet("background: transparent; border: none; color: #111;")
        self.btn_back.clicked.connect(self.back_clicked.emit)
        footer.addWidget(self.btn_back)
        lay.addLayout(footer)

        root.addWidget(card, 1)

    def update_language(self):
        self.lbl_title.setText(t("settings_dev.title"))
        self.btn_register.setText(t("settings_dev.register"))
        self.btn_topup.setText(t("settings_dev.topup"))
        self.btn_back.setText(t("settings_dev.back"))
