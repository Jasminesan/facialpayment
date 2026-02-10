from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDoubleValidator, QIntValidator

from ui.ui_config import AppConfig, t


class TopUpView(QWidget):
    """หน้าเติมเงิน — ค้นหาผู้ใช้ด้วย ID แล้วเติมเงิน"""

    back_clicked = Signal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._found_user = None
        self.init_ui()

    # ================================================================
    # UI
    # ================================================================
    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ---- Header ----
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #2196F3;")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        btn_back = QPushButton(t("topup.back"))
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        btn_back.clicked.connect(self.back_clicked.emit)
        h_lay.addWidget(btn_back)

        lbl_title = QLabel(t("topup.title"))
        lbl_title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; background: transparent;")
        lbl_title.setAlignment(Qt.AlignCenter)
        h_lay.addWidget(lbl_title, 1)
        h_lay.addSpacing(60)

        root.addWidget(header)

        # ---- Scrollable content ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # -- ค้นหาผู้ใช้ --
        search_group = QGroupBox(t("topup.search_group"))
        search_group.setStyleSheet(self._group_style())
        s_lay = QHBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("topup.search_hint"))
        self.search_input.setValidator(QIntValidator(1, 999999))
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.returnPressed.connect(self.search_user)
        s_lay.addWidget(self.search_input)

        self.btn_search = self._make_btn(t("topup.search_btn"), "#2196F3", width=140)
        self.btn_search.clicked.connect(self.search_user)
        s_lay.addWidget(self.btn_search)

        layout.addWidget(search_group)

        # -- ข้อมูลผู้ใช้ --
        info_group = QGroupBox(t("topup.info_group"))
        info_group.setStyleSheet(self._group_style())
        info_form = QFormLayout(info_group)
        info_form.setSpacing(10)

        self.lbl_name = QLabel("—")
        self.lbl_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_form.addRow(t("topup.name"), self.lbl_name)

        self.lbl_uid = QLabel("—")
        self.lbl_uid.setStyleSheet("font-size: 16px; color: #555;")
        info_form.addRow(t("topup.uid"), self.lbl_uid)

        self.lbl_balance = QLabel("—")
        self.lbl_balance.setStyleSheet("font-size: 22px; font-weight: bold; color: #4CAF50;")
        info_form.addRow(t("topup.balance"), self.lbl_balance)

        layout.addWidget(info_group)

        # -- จำนวนเงิน --
        topup_group = QGroupBox(t("topup.amount_group"))
        topup_group.setStyleSheet(self._group_style())
        t_lay = QVBoxLayout(topup_group)

        quick_lbl = QLabel(t("topup.quick"))
        quick_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        t_lay.addWidget(quick_lbl)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(10)
        for amt in [50, 100, 200, 500, 1000]:
            b = self._make_btn(f"฿{amt}", "#E3F2FD", text_color="#1565C0")
            b.setFixedHeight(50)
            b.clicked.connect(lambda _, a=amt: self.topup_input.setText(f"{a:.2f}"))
            quick_row.addWidget(b)
        t_lay.addLayout(quick_row)

        custom_row = QHBoxLayout()
        lbl_c = QLabel(t("topup.custom"))
        lbl_c.setStyleSheet("font-size: 14px; font-weight: bold;")
        custom_row.addWidget(lbl_c)

        self.topup_input = QLineEdit()
        self.topup_input.setPlaceholderText("0.00")
        self.topup_input.setValidator(QDoubleValidator(1, 999999, 2))
        self.topup_input.setFixedWidth(200)
        self.topup_input.setStyleSheet(self._input_style())
        custom_row.addWidget(self.topup_input)
        custom_row.addStretch()
        t_lay.addLayout(custom_row)

        layout.addWidget(topup_group)

        # -- ปุ่มเติมเงิน --
        self.btn_topup = self._make_btn(t("topup.do"), "#4CAF50")
        self.btn_topup.setFixedHeight(52)
        self.btn_topup.setEnabled(False)
        self.btn_topup.clicked.connect(self.do_topup)
        layout.addWidget(self.btn_topup)

        # -- ผลลัพธ์ --
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("font-size: 16px; padding: 8px;")
        layout.addWidget(self.result_label)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def update_language(self):
        # update dynamic texts
        # header
        # placeholders and button labels
        # We only created some labels via t() already, so set button texts
        self.btn_topup.setText(t("topup.do"))
        self.btn_search.setText(t("topup.search_btn"))
        self.search_input.setPlaceholderText(t("topup.search_hint"))
        # group titles are created with t() initially
    # ================================================================
    # Logic
    # ================================================================
    def search_user(self):
        uid = self.search_input.text().strip()
        if not uid:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกรหัสผู้ใช้")
            return

        user = self.db.get_user_by_id(uid)
        if user:
            self._found_user = user
            self.lbl_name.setText(user.get("name", "ไม่ทราบ"))
            self.lbl_uid.setText(str(user.get("user_id", uid)))
            bal = float(user.get("balance", 0))
            self.lbl_balance.setText(f"฿{bal:,.2f}")
            self.btn_topup.setEnabled(True)
            self.result_label.setText("")
        else:
            self._found_user = None
            self.lbl_name.setText("—")
            self.lbl_uid.setText("—")
            self.lbl_balance.setText("—")
            self.btn_topup.setEnabled(False)
            QMessageBox.warning(self, "ไม่พบผู้ใช้", f"ไม่พบผู้ใช้รหัส \"{uid}\" ในระบบ")

    def do_topup(self):
        uid = self.search_input.text().strip()
        amt_text = self.topup_input.text().strip()

        if not amt_text:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกจำนวนเงินที่ต้องการเติม")
            return
        try:
            amount = float(amt_text)
        except ValueError:
            QMessageBox.warning(self, "ข้อมูลผิดพลาด", "จำนวนเงินไม่ถูกต้อง")
            return
        if amount <= 0:
            QMessageBox.warning(self, "ข้อมูลผิดพลาด", "จำนวนเงินต้องมากกว่า 0")
            return

        name = self.lbl_name.text()
        reply = QMessageBox.question(
            self, "ยืนยันเติมเงิน",
            f"เติมเงิน ฿{amount:,.2f} ให้ \"{name}\" ใช่หรือไม่?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            result = self.db.top_up_balance(uid, amount)
            if result.get("success"):
                new_bal = result["new_balance"]
                self.lbl_balance.setText(f"฿{new_bal:,.2f}")
                self.topup_input.clear()
                self.result_label.setText(f"✅  เติมเงินสำเร็จ!  ยอดใหม่: ฿{new_bal:,.2f}")
                self.result_label.setStyleSheet("font-size: 16px; color: #2E7D32; font-weight: bold; padding: 8px;")
            else:
                self.result_label.setText(f"❌  {result.get('error', 'ไม่ทราบสาเหตุ')}")
                self.result_label.setStyleSheet("font-size: 16px; color: #C62828; font-weight: bold; padding: 8px;")
        except Exception as e:
            QMessageBox.critical(self, "ผิดพลาด", str(e))

    def reset_view(self):
        """เรียกเมื่อกลับมาหน้านี้ใหม่"""
        self.search_input.clear()
        self.topup_input.clear()
        self.lbl_name.setText("—")
        self.lbl_uid.setText("—")
        self.lbl_balance.setText("—")
        self.btn_topup.setEnabled(False)
        self.result_label.setText("")
        self._found_user = None

    # ================================================================
    # Style helpers
    # ================================================================
    @staticmethod
    def _group_style():
        return """
            QGroupBox {
                font-size: 16px; font-weight: bold;
                border: 2px solid #e0e0e0; border-radius: 10px;
                margin-top: 12px; padding-top: 16px; background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #333;
            }
        """

    @staticmethod
    def _input_style():
        return """
            QLineEdit {
                border: 2px solid #e0e0e0; border-radius: 8px;
                padding: 10px 14px; font-size: 15px; background: #fafafa;
            }
            QLineEdit:focus { border-color: #2196F3; background: white; }
        """

    @staticmethod
    def _make_btn(text, color, text_color="white", width=None):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(44)
        if width:
            btn.setFixedWidth(width)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: {text_color};
                font-weight: bold; font-size: 15px;
                border-radius: 10px; border: none; padding: 6px 14px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:disabled {{ background-color: #bdbdbd; color: #eee; }}
        """)
        return btn
