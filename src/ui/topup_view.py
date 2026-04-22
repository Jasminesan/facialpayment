from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.ui_config import AppConfig, t


class TopUpView(QWidget):
    back_clicked = Signal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        self._found_user = None
        self._amount_stack = []
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
        lay.setContentsMargins(28, 26, 28, 26)
        lay.setSpacing(18)

        top_row = QHBoxLayout()
        self.lbl_title = QLabel(t("topup.title_plain"))
        self.lbl_title.setFont(QFont(AppConfig.FONT_FAMILY, 32, QFont.Weight.Bold))
        self.lbl_title.setStyleSheet("color: #111;")
        top_row.addWidget(self.lbl_title)

        top_row.addStretch()
        self.lbl_total = QLabel("0 THB")
        self.lbl_total.setFont(QFont(AppConfig.FONT_FAMILY, 36, QFont.Weight.Bold))
        self.lbl_total.setStyleSheet("color: #111;")
        top_row.addWidget(self.lbl_total)
        lay.addLayout(top_row)

        self.lbl_user = QLabel("-")
        self.lbl_user.setFont(QFont(AppConfig.FONT_FAMILY, 16))
        self.lbl_user.setStyleSheet("color: #555;")
        lay.addWidget(self.lbl_user)

        rows = [
            ((10, "#D9B957"), (20, "#66A266"), (50, "#6E7DB8")),
            ((100, "#D66567"), (500, "#9174AF"), (None, "#3C3C3C")),
        ]

        for row in rows:
            row_l = QHBoxLayout()
            row_l.setSpacing(16)
            for value, color in row:
                if value is None:
                    b = self._make_button(t("topup.del"), color)
                    b.clicked.connect(self._on_delete)
                else:
                    b = self._make_button(str(value), color)
                    b.clicked.connect(lambda _, amt=value: self._push_amount(amt))
                row_l.addWidget(b)
            lay.addLayout(row_l)

        action_row = QHBoxLayout()
        action_row.setSpacing(20)

        self.btn_cancel = self._make_button(t("topup.cancel"), "#D74646", height=72)
        self.btn_cancel.clicked.connect(self.back_clicked.emit)
        action_row.addWidget(self.btn_cancel)

        self.btn_confirm = self._make_button(t("topup.confirm"), "#8BC34A", text_color="#111", height=72)
        self.btn_confirm.clicked.connect(self._confirm_topup)
        action_row.addWidget(self.btn_confirm)

        lay.addLayout(action_row)
        root.addWidget(card, 1)

    def set_user(self, user_data: dict):
        self._found_user = user_data
        self._amount_stack = []

        if not user_data:
            self.lbl_user.setText("-")
            self._refresh_total()
            return

        user_id = str(user_data.get("user_id", "-"))
        name = user_data.get("name", "-")
        balance = float(user_data.get("balance", 0.0))
        self.lbl_user.setText(f"{name} ({user_id}) • {t('topup.balance_short')}: {balance:,.2f} THB")
        self._refresh_total()

    def _push_amount(self, amount: int):
        self._amount_stack.append(float(amount))
        self._refresh_total()

    def _on_delete(self):
        if self._amount_stack:
            self._amount_stack.pop()
            self._refresh_total()

    def _refresh_total(self):
        total = int(sum(self._amount_stack))
        self.lbl_total.setText(f"{total} THB")

    def _confirm_topup(self):
        if not self._found_user:
            QMessageBox.warning(self, t("topup.title_plain"), t("topup.err_no_user"))
            return

        total = float(sum(self._amount_stack))
        if total <= 0:
            QMessageBox.warning(self, t("topup.title_plain"), t("topup.err_no_amount"))
            return

        uid = str(self._found_user.get("user_id", "")).strip()
        result = self.db.top_up_balance(uid, total)
        if result.get("success"):
            new_balance = float(result.get("new_balance", 0.0))
            self._found_user["balance"] = new_balance
            self._amount_stack = []
            self._refresh_total()
            self.set_user(self._found_user)
            QMessageBox.information(
                self,
                t("topup.title_plain"),
                t("topup.success", amt=f"{total:,.0f}", bal=f"{new_balance:,.2f}"),
            )
        else:
            QMessageBox.warning(self, t("topup.title_plain"), result.get("error", t("topup.err_unknown")))

    def reset_view(self):
        self._found_user = None
        self._amount_stack = []
        self.lbl_user.setText("-")
        self._refresh_total()

    def update_language(self):
        self.lbl_title.setText(t("topup.title_plain"))
        self.btn_cancel.setText(t("topup.cancel"))
        self.btn_confirm.setText(t("topup.confirm"))
        if self._found_user:
            self.set_user(self._found_user)

    @staticmethod
    def _make_button(text, bg, text_color="white", height=64):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(height)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFont(QFont(AppConfig.FONT_FAMILY, 22, QFont.Weight.Medium))
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }}
            QPushButton:pressed {{ background-color: #2D2D2D; }}
            """
        )
        return btn
