from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Slot

# Import Config
from ui.ui_config import AppConfig

# Import Views ทั้งหมด
from ui.home_view import HomeView
from ui.scan_view import ScanView
from ui.confirm_view import ConfirmView
from ui.success_view import SuccessView
from ui.no_result_view import NoResultView
from ui.settings_view import SettingsView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biometric Payment System")
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_GRAY};")

        
        self.resize(700, 700)
        # self.showFullScreen() #Run on  Raspberry Pi 

        # 1. Setup Stacked Widget 
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # 2. สร้าง Instance ของหน้าจอต่างๆ
        self.view_home = HomeView()
        self.view_scan = ScanView()
        self.view_confirm = ConfirmView()
        self.view_success = SuccessView()
        self.view_no_result = NoResultView()
        self.view_settings = SettingsView()

        # 3. เพิ่มหน้าจอเข้า Stack
        self.stack.addWidget(self.view_home)      # Index 0
        self.stack.addWidget(self.view_scan)      # Index 1
        self.stack.addWidget(self.view_confirm)   # Index 2
        self.stack.addWidget(self.view_success)   # Index 3
        self.stack.addWidget(self.view_no_result) # Index 4
        self.stack.addWidget(self.view_settings)  # Index 5

        # 4. เชื่อมต่อ Flow การทำงาน (Signal -> Slot)
        self.setup_connections()

        # เริ่มต้นที่หน้า Home
        self.stack.setCurrentWidget(self.view_home)

    def setup_connections(self):
        # --- HOME VIEW FLOW ---
        # กดปุ่ม Settings -> ไปหน้า Settings
        self.view_home.settings_clicked.connect(lambda: self.switch_to(self.view_settings))
        # กดหน้าจอเพื่อเริ่ม -> ไปหน้า Scan
        self.view_home.start_clicked.connect(self.start_scan_process)

        # --- SETTINGS VIEW FLOW ---
        # กด Back -> กลับ Home
        self.view_settings.back_clicked.connect(lambda: self.switch_to(self.view_home))
        # เปลี่ยนภาษา (Logic จำลอง)
        self.view_settings.language_changed.connect(self.on_language_changed)

        # --- SCAN VIEW FLOW ---
        # สแกนเจอ -> ไปหน้า Confirm
        self.view_scan.scanned_success.connect(self.on_scan_success)
        # สแกนไม่เจอ -> ไปหน้า No Result
        self.view_scan.scanned_fail.connect(lambda: self.switch_to(self.view_no_result))

        # --- NO RESULT FLOW ---
        # กด Try Again -> กลับไป Scan ใหม่
        self.view_no_result.retry_clicked.connect(self.start_scan_process)

        # --- CONFIRM VIEW FLOW ---
        # กด OK (ยืนยันจ่าย) -> ตัดเงิน -> ไปหน้า Success
        self.view_confirm.confirm_clicked.connect(self.process_payment)
        # กด Cancel -> ยกเลิกกลับบ้าน
        self.view_confirm.cancel_clicked.connect(lambda: self.switch_to(self.view_home))

        # --- SUCCESS VIEW FLOW ---
        # แสดงผลครบ 3 วิ -> กลับบ้านอัตโนมัติ
        self.view_success.finished.connect(lambda: self.switch_to(self.view_home))

    def switch_to(self, widget):
        self.stack.setCurrentWidget(widget)

    def start_scan_process(self):
        self.view_scan.start_scanning()
        self.switch_to(self.view_scan)

    def on_scan_success(self, user_data):
        name = user_data.get("name", "Unknown User")
        balance = user_data.get("balance", 0.0)
        
        current_bill_amount = 60.0 
        
        self.view_confirm.set_user_data(name, balance, current_bill_amount)
        self.switch_to(self.view_confirm)

    def process_payment(self):
        # TODO: เรียก Service เพื่อตัดเงินใน Database จริงๆ ตรงนี้
        
        print("Payment Processed Successfully!")
        
        user_name = self.view_confirm.lbl_name.text()
        self.view_success.set_user_name(user_name)
        
        self.switch_to(self.view_success)

    def on_language_changed(self, lang):
        print(f"Language changed to: {lang}")
        # TODO: เพิ่ม Logic เปลี่ยนภาษาของ UI ตรงนี้ในอนาคต