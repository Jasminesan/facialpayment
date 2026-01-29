from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt, Signal, QThread
from ui.ui_config import AppConfig
from database.connector import DatabaseHandler  


class PaymentWorker(QThread):
    finished = Signal(bool, object) # ส่งค่ากลับ (สำเร็จไหม, ข้อมูล/Error)

    def __init__(self, db, user_id, amount):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.amount = amount

    def run(self):
        try:
            # เรียกใช้ฟังก์ชันตัดเงิน (ทำงานหลังบ้าน ไม่กวนหน้าจอ)
            print(f"🔄 Worker: Processing payment for {self.user_id}...")
            
            # ⚠️ หมายเหตุ: ตรวจสอบ DatabaseHandler ว่ารับ parameter อะไรบ้าง
            # ในโค้ดก่อนหน้าเรารับแค่ (user_id, amount) 
            result = self.db.process_payment(self.user_id, self.amount)
            
            # ตรวจสอบผลลัพธ์จาก Dict ที่ได้กลับมา
            if result.get("success"):
                self.finished.emit(True, result)
            else:
                self.finished.emit(False, result.get("error", "Unknown Error"))
                
        except Exception as e:
            print(f"❌ Worker Error: {e}")
            self.finished.emit(False, str(e))

# ==========================================
# 2. ปรับปรุง Class ConfirmView
# ==========================================
class ConfirmView(QWidget):
    payment_success = Signal(dict) 
    cancel_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.db = DatabaseHandler()
        self.current_user_id = None
        self.payment_amount = 0.0
        self.worker = None # ตัวแปรสำหรับเก็บ Thread
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

        self.btn_ok = QPushButton("CONFIRM PAY")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.setStyleSheet(f"background-color: {AppConfig.COLOR_BTN_GREEN}; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        
        # เชื่อมปุ่มเข้ากับฟังก์ชันเริ่ม Thread
        self.btn_ok.clicked.connect(self.start_payment_thread)

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"background-color: {AppConfig.COLOR_BTN_RED}; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_cancel.clicked.connect(self.cancel_clicked.emit)

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(btn_cancel)

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
        
        # รีเซ็ตปุ่มให้พร้อมกดใหม่เสมอ
        self.btn_ok.setText("CONFIRM PAY")
        self.btn_ok.setEnabled(True)

    # 3. ฟังก์ชันเริ่มทำงาน (Start)
    def start_payment_thread(self):
        if not self.current_user_id:
            return

        # ล็อคปุ่มกันกดซ้ำ
        self.btn_ok.setEnabled(False)
        self.btn_ok.setText("Processing...")
        
        print(f"💰 Starting Thread for: {self.payment_amount} THB")

        # สร้างและรัน Worker Thread
        self.worker = PaymentWorker(self.db, self.current_user_id, self.payment_amount)
        self.worker.finished.connect(self.handle_payment_result)
        self.worker.start()

    # 4. ฟังก์ชันรับผลลัพธ์ (Callback)
    def handle_payment_result(self, is_success, result_data):
        # คืนค่าปุ่ม
        self.btn_ok.setEnabled(True)
        self.btn_ok.setText("CONFIRM PAY")

        if is_success:
            print("✅ Payment Success (Thread)!")
            # ส่งข้อมูลไปหน้า Success
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
            QMessageBox.critical(self, "Payment Error", f"เกิดข้อผิดพลาด: {result_data}")