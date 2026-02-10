from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal
from ui.ui_config import AppConfig, t, get_lang

class SettingsView(QWidget):
    back_clicked = Signal()
    language_changed = Signal(str)
    register_clicked = Signal()
    topup_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # หัวข้อ + ปุ่ม Admin
        top_row = QHBoxLayout()
        self.lbl_title = QLabel(t("settings.title"))
        self.lbl_title.setFont(QFont(AppConfig.FONT_FAMILY, 32, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("background-color: transparent;")
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()
        # Visible Admin toggle/button
        self.btn_admin = QPushButton(t("settings.admin"))
        self.btn_admin.setFlat(True)
        self.btn_admin.setFont(QFont(AppConfig.FONT_FAMILY, 16))
        self.btn_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_admin.setStyleSheet("color: #444444; background-color: transparent;")
        self.btn_admin.clicked.connect(self._toggle_admin)
        top_row.addWidget(self.btn_admin)
        layout.addLayout(top_row)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(line)

        layout.addSpacing(20)
        # Language panel (hidden when admin-mode shows register/topup)
        self.lang_container = QWidget()
        lang_v = QVBoxLayout(self.lang_container)
        lang_v.setContentsMargins(0, 0, 0, 0)
        self.lbl_lang = QLabel(t("settings.language"))
        self.lbl_lang.setFont(QFont(AppConfig.FONT_FAMILY, 24))
        self.lbl_lang.setStyleSheet("background-color: transparent;")
        lang_v.addWidget(self.lbl_lang)

        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(30)
        lang_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.btn_eng = self.create_lang_btn("ENG", active=(get_lang() == 'ENG'))
        self.btn_eng.clicked.connect(lambda: self.set_language("ENG"))
        
        self.btn_tha = self.create_lang_btn("THA", active=(get_lang() == 'THA'))
        self.btn_tha.clicked.connect(lambda: self.set_language("THA"))

        lang_layout.addWidget(self.btn_eng)
        lang_layout.addWidget(self.btn_tha)
        lang_v.addLayout(lang_layout)
        layout.addWidget(self.lang_container)

        # Admin action container (register / top-up) - hidden by default
        self.admin_container = QWidget()
        admin_layout = QHBoxLayout(self.admin_container)
        admin_layout.setSpacing(60)
        admin_layout.setContentsMargins(20, 20, 20, 20)

        self.btn_register_big = QPushButton("REGISTER")
        self.btn_register_big.setFont(QFont(AppConfig.FONT_FAMILY, 28, QFont.Weight.Bold))
        self.btn_register_big.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_register_big.setStyleSheet("background: transparent; border: none; color: black;")
        self.btn_register_big.clicked.connect(self.register_clicked.emit)

        self.btn_topup_big = QPushButton("TOP-UP")
        self.btn_topup_big.setFont(QFont(AppConfig.FONT_FAMILY, 28, QFont.Weight.Bold))
        self.btn_topup_big.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_topup_big.setStyleSheet("background: transparent; border: none; color: black;")
        self.btn_topup_big.clicked.connect(self.topup_clicked.emit)

        admin_layout.addWidget(self.btn_register_big)
        admin_layout.addStretch()
        admin_layout.addWidget(self.btn_topup_big)
        self.admin_container.setVisible(False)
        layout.addWidget(self.admin_container)

        layout.addStretch()

        btn_back_layout = QHBoxLayout()
        btn_back_layout.addStretch()
        
        self.btn_back = QPushButton(t("settings.back"))
        self.btn_back.setFlat(True)
        self.btn_back.setFont(QFont(AppConfig.FONT_FAMILY, 20))
        self.btn_back.setStyleSheet(f"color: {AppConfig.COLOR_TEXT_MAIN}; text-align: right; background-color: transparent;")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_clicked.emit)
        
        btn_back_layout.addWidget(self.btn_back)
        layout.addLayout(btn_back_layout)

    def update_language(self):
        self.lbl_title.setText(t("settings.title"))
        self.lbl_lang.setText(t("settings.language"))
        if hasattr(self, 'btn_admin'):
            self.btn_admin.setText(t("settings.admin"))
        if hasattr(self, 'btn_register_big'):
            self.btn_register_big.setText(t("home.register"))
        if hasattr(self, 'btn_topup_big'):
            self.btn_topup_big.setText(t("home.topup"))
        self.btn_back.setText(t("settings.back"))
        # Update language button styles according to current language
        # Caller (MainWindow) will call set_lang() globally, and this emits language_changed

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

    def set_admin_mode(self, enabled: bool):
        """Show large REGISTER / TOP-UP when enabled. Hide language controls."""
        self.admin_container.setVisible(enabled)
        self.lang_container.setVisible(not enabled)

    def _toggle_admin(self):
        """Toggle admin container visibility from the visible Admin button."""
        try:
            cur = self.admin_container.isVisible()
            # show admin actions and hide language controls when enabled
            self.admin_container.setVisible(not cur)
            self.lang_container.setVisible(cur)
        except Exception:
            pass