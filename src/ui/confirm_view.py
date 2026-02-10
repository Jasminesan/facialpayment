from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal, QThread
from ui.ui_config import AppConfig, t
from database.connector import DatabaseHandler  


class PaymentWorker(QThread):
    finished = Signal(bool, object)

    def __init__(self, db, user_id, amount):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.amount = amount

    def run(self):
        try:
            print(f"🔄 Worker: กำลังตัดเงิน {self.user_id}...")
            result = self.db.process_payment(self.user_id, self.amount)
            if result.get("success"):
                self.finished.emit(True, result)
            else:
                self.finished.emit(False, result.get("error", "Unknown Error"))
        except Exception as e:
            print(f"❌ Worker Error: {e}")
            self.finished.emit(False, str(e))


class ConfirmView(QWidget):
    payment_success = Signal(dict) 
    cancel_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.db = DatabaseHandler()
        self.current_user_id = None
        self.payment_amount = 0.0
        self.worker = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN}; color: {AppConfig.COLOR_TEXT_MAIN};")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 50, 30, 50)
        main_layout.setSpacing(15)

        self.lbl_name = QLabel(t("confirm.loading"))
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
        
        def create_row(label_key):
            row = QHBoxLayout()
            l = QLabel(t(label_key))
            v = QLabel("0.00")
            l.setStyleSheet("font-size: 18px; background-color: transparent;")
            v.setStyleSheet("font-size: 24px; font-weight: bold; background-color: transparent;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            return row, l, v

        row1, self.lbl_balance_label, self.lbl_total = create_row("confirm.balance")
        row2, self.lbl_amount_label, self.lbl_pay = create_row("confirm.amount")

        info_layout.addLayout(row1)
        info_layout.addLayout(row2)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.btn_ok = QPushButton(t("confirm.ok"))
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.setStyleSheet(f"background-color: {AppConfig.COLOR_BTN_GREEN}; color: white; font-weight: bold; padding: 10px; border-radius: 5px; font-size: 16px;")
        self.btn_ok.clicked.connect(self.start_payment_thread)

        self.btn_cancel = QPushButton(t("confirm.cancel"))
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(f"background-color: {AppConfig.COLOR_BTN_RED}; color: white; font-weight: bold; padding: 10px; border-radius: 5px; font-size: 16px;")
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)

        main_layout.addWidget(self.lbl_name)
        main_layout.addLayout(avatar_container)
        main_layout.addSpacing(20)
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def set_user_data(self, user_id, name, balance, amount): 
        self.current_user_id = user_id 
        self.payment_amount = amount   
        
        self.lbl_name.setText(name)
        self.lbl_total.setText(f"{balance:,.2f}")
        self.lbl_pay.setText(f"{amount:,.2f}")
        
        self.btn_ok.setText(t("confirm.ok"))
        self.btn_ok.setEnabled(True)

    def start_payment_thread(self):
        if not self.current_user_id:
            return

        self.btn_ok.setEnabled(False)
        self.btn_ok.setText(t("confirm.processing"))
        
        print(f"💰 Starting Thread for: {self.payment_amount} THB")

        self.worker = PaymentWorker(self.db, self.current_user_id, self.payment_amount)
        self.worker.finished.connect(self.handle_payment_result)
        self.worker.start()

    def handle_payment_result(self, is_success, result_data):
        self.btn_ok.setEnabled(True)
        self.btn_ok.setText(t("confirm.ok"))

        if is_success:
            print("✅ Payment Success (Thread)!")
            receipt = {
                "user_name": result_data.get("user_name", self.lbl_name.text()),
                "amount": self.payment_amount
            }
            final_data = {
                "receipt": receipt,
                "new_balance": result_data.get("new_balance", 0.0)
            }
            self.payment_success.emit(final_data)
        else:
            print(f"❌ Payment Failed: {result_data}")
            QMessageBox.critical(self, t("confirm.fail_title"), f"เกิดข้อผิดพลาด: {result_data}")

    def update_language(self):
        self.lbl_balance_label.setText(t("confirm.balance"))
        self.lbl_amount_label.setText(t("confirm.amount"))
        self.btn_ok.setText(t("confirm.ok"))
        self.btn_cancel.setText(t("confirm.cancel"))