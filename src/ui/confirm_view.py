from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from ui.ui_config import AppConfig

class ConfirmView(QWidget):
    confirm_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 50, 30, 50)
        main_layout.setSpacing(15)

        self.lbl_name = QLabel("Loading Name...")
        self.lbl_name.setStyleSheet("font-size: 32px; font-weight: bold; background-color: transparent;")
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(120, 120)
        self.lbl_avatar.setStyleSheet("background-color: #D3D3D3; border-radius: 60px;")
        
        avatar_container = QHBoxLayout()
        avatar_container.addStretch()
        avatar_container.addWidget(self.lbl_avatar)
        avatar_container.addStretch()

        info_layout = QVBoxLayout()
        
        def create_row(label):
            row = QHBoxLayout()
            l = QLabel(label)
            v = QLabel("0.00")
            l.setStyleSheet("font-size: 18px; background-color: transparent;")
            v.setStyleSheet("font-size: 24px; font-weight: bold; background-color: transparent;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            return row, v

        row1, self.lbl_total = create_row("Total Balance")
        row2, self.lbl_pay = create_row("Payment Amount")

        info_layout.addLayout(row1)
        info_layout.addLayout(row2)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        btn_ok = QPushButton("OK")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(f"background-color: {AppConfig.COLOR_BTN_GREEN}; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_ok.clicked.connect(self.confirm_clicked.emit)

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"background-color: {AppConfig.COLOR_BTN_RED}; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_cancel.clicked.connect(self.cancel_clicked.emit)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        main_layout.addWidget(self.lbl_name)
        main_layout.addLayout(avatar_container)
        main_layout.addSpacing(20)
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def set_user_data(self, name, balance, amount):
        self.lbl_name.setText(name)
        self.lbl_total.setText(f"{balance:,.2f}")
        self.lbl_pay.setText(f"{amount:,.2f}")