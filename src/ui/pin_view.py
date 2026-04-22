from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal

from ui.ui_config import AppConfig, t


class PinView(QWidget):
    back_clicked = Signal()
    pin_submitted = Signal(str)

    def __init__(self):
        super().__init__()
        self.entered_pin = ""
        self.max_len = 6
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
        lay.setContentsMargins(30, 26, 30, 26)
        lay.setSpacing(20)

        top = QHBoxLayout()
        self.lbl_title = QLabel(t("pin.title"))
        self.lbl_title.setFont(QFont(AppConfig.FONT_FAMILY, 30, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #111;")
        top.addWidget(self.lbl_title)
        lay.addLayout(top)

        pin_header = QHBoxLayout()
        pin_header.setSpacing(8)

        left_placeholder = QLabel("")
        left_placeholder.setFixedWidth(140)
        pin_header.addWidget(left_placeholder)

        pin_header.addStretch()
        self.lbl_mask = QLabel("")
        self.lbl_mask.setFont(QFont(AppConfig.FONT_FAMILY, 34, QFont.Weight.Bold))
        self.lbl_mask.setStyleSheet("color: #111;")
        self.lbl_mask.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_header.addWidget(self.lbl_mask)
        pin_header.addStretch()

        self.btn_back = QPushButton(t("pin.back"))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setMinimumWidth(140)
        self.btn_back.setFont(QFont(AppConfig.FONT_FAMILY, 18))
        self.btn_back.setStyleSheet("background: transparent; border: none; color: #222;")
        self.btn_back.clicked.connect(self.back_clicked.emit)
        pin_header.addWidget(self.btn_back)
        lay.addLayout(pin_header)

        keypad = QVBoxLayout()
        keypad.setSpacing(12)
        rows = [("1", "2", "3"), ("4", "5", "6"), ("7", "8", "9")]

        for row in rows:
            row_lay = QHBoxLayout()
            row_lay.setSpacing(14)
            for n in row:
                row_lay.addWidget(self._make_key_btn(n, "#383A3F"))
            keypad.addLayout(row_lay)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(14)
        self.btn_del = self._make_key_btn(t("pin.del"), "#F44336")
        self.btn_del.clicked.connect(self._on_delete)
        bottom_row.addWidget(self.btn_del)

        bottom_row.addWidget(self._make_key_btn("0", "#383A3F"))

        self.btn_ok = self._make_key_btn(t("pin.ok"), "#8BC34A", text_color="#111")
        self.btn_ok.clicked.connect(self._submit_pin)
        bottom_row.addWidget(self.btn_ok)
        keypad.addLayout(bottom_row)

        lay.addLayout(keypad)

        root.addWidget(card, 1)
        root.addStretch()

    def _make_key_btn(self, text, bg, text_color="white"):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumSize(110, 64)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setFont(QFont(AppConfig.FONT_FAMILY, 22, QFont.Weight.Medium))
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:pressed {{ background-color: #222; }}
            """
        )
        if text.isdigit():
            btn.clicked.connect(lambda _, d=text: self._append_digit(d))
        return btn

    def _append_digit(self, digit):
        if len(self.entered_pin) >= self.max_len:
            return
        self.entered_pin += digit
        self._refresh_mask()

    def _on_delete(self):
        self.entered_pin = self.entered_pin[:-1]
        self._refresh_mask()

    def _refresh_mask(self):
        self.lbl_mask.setText("✱" * len(self.entered_pin))

    def _submit_pin(self):
        self.pin_submitted.emit(self.entered_pin)

    def clear_pin(self):
        self.entered_pin = ""
        self._refresh_mask()

    def update_language(self):
        self.lbl_title.setText(t("pin.title"))
        self.btn_back.setText(t("pin.back"))
        self.btn_del.setText(t("pin.del"))
        self.btn_ok.setText(t("pin.ok"))
