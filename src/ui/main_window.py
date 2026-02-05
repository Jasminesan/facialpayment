from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Slot, Qt

from ui.ui_config import AppConfig

# Import Views
from ui.home_view import HomeView
from ui.scan_view import ScanView
from ui.confirm_view import ConfirmView
from ui.success_view import SuccessView
from ui.no_result_view import NoResultView
from ui.settings_view import SettingsView

# Import Services
from services.pos_macropad import MacroPadListener
from services.camera import CameraService
from database.connector import DatabaseHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biometric Payment System")
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_GRAY};")
        
       
        self.showFullScreen() 
        
        self.db = DatabaseHandler() 
        self.current_bill_amount = 0.0

        print("📷 Initializing Camera Service...")
        self.camera_service = CameraService()
        try:
            self.camera_service.start() 
            print("✅ Camera Started in Background!")
        except Exception as e:
            print(f"❌ Camera Init Error: {e}")

        print("📡 Starting Real-time Sync...")
        # buffer for updates that arrive before views/matchers are ready
        self._pending_face_users = None
        try:
            # keep the listener registration so it is not garbage-collected
            self.user_listener = self.db.listen_for_updates(self.update_face_database)
        except AttributeError:
            print("⚠️ Warning: DatabaseHandler might not have 'listen_for_updates' yet.")

        # เริ่มระบบรับค่าจาก POS (MacroPad USB-Serial)
        try:
            # auto-detect the MacroPad USB-Serial device; set baud to 115200 (ignored for CDC but harmless)
            self.serial_thread = MacroPadListener(port=None, baud=115200, auto_detect=True)
            self.serial_thread.payment_received.connect(self.on_pos_trigger)
            self.serial_thread.start()
            print("✅ MacroPadListener (POS) Started!")
        except Exception as e:
            print(f"❌ MacroPad Init Error: {e}")

        # Setup Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Create Views
        self.view_home = HomeView()
        self.view_scan = ScanView(self.camera_service)
        self.view_confirm = ConfirmView() 
        self.view_success = SuccessView()
        self.view_no_result = NoResultView()
        self.view_settings = SettingsView()

        # Add Views to Stack
        self.stack.addWidget(self.view_home)
        self.stack.addWidget(self.view_scan)
        self.stack.addWidget(self.view_confirm)
        self.stack.addWidget(self.view_success)
        self.stack.addWidget(self.view_no_result)
        self.stack.addWidget(self.view_settings)

        self.setup_connections()
        self.stack.setCurrentWidget(self.view_home)

        # If there was a pending face DB update before ScanView was created, apply it now
        if self._pending_face_users:
            try:
                if getattr(self.view_scan, 'matcher', None):
                    self.view_scan.matcher.load_users_from_data(self._pending_face_users)
                    print(f"✅ Applied pending face DB ({len(self._pending_face_users)} users) to ScanView.matcher")
                self._pending_face_users = None
            except Exception as e:
                print(f"❌ Failed to apply pending face DB to matcher: {e}")

    def setup_connections(self):
        # Home -> Settings
        self.view_home.settings_clicked.connect(self.go_to_settings)
        self.view_home.start_clicked.connect(self.start_scan_process)
        
        # Settings -> Home
        self.view_settings.back_clicked.connect(lambda: self.switch_to(self.view_home))
        self.view_settings.language_changed.connect(self.on_language_changed)

        # Scan Logic
        self.view_scan.scanned_success.connect(self.on_scan_success)
        self.view_scan.scanned_fail.connect(lambda: self.switch_to(self.view_no_result))
        
        # Retry Logic
        self.view_no_result.retry_clicked.connect(self.start_scan_process)

        # Confirm & Payment Logic
        self.view_confirm.payment_success.connect(self.on_payment_complete)
        self.view_confirm.cancel_clicked.connect(lambda: self.switch_to(self.view_home))
        self.view_success.finished.connect(lambda: self.switch_to(self.view_home))

    def switch_to(self, widget):
        self.stack.setCurrentWidget(widget)

    def go_to_settings(self):
        """ฟังก์ชันเข้าหน้า Setting แบบปลอดภัย"""
        print("⚙️ Opening Settings...")
        # หยุดกล้องก่อนเสมอ ไม่งั้น Pi ค้าง
        if hasattr(self.view_scan, 'stop_camera'):
             self.view_scan.stop_camera()
        
        self.switch_to(self.view_settings)

    def start_scan_process(self):
        self.view_scan.start_scanning() 
        self.switch_to(self.view_scan)

    def update_face_database(self, users_list):
        # โหลดข้อมูลหน้าเข้า RAM (ทำใน Thread หรือ Callback)
        print(f"🔄 Updating Face Matcher with {len(users_list)} users...")
        updated = False

        # Prefer updating ScanView's matcher (ScanView creates its own FaceMatcher)
        if hasattr(self, 'view_scan') and getattr(self.view_scan, 'matcher', None):
            try:
                self.view_scan.matcher.load_users_from_data(users_list)
                print("✅ Face Database Updated in ScanView.matcher")
                updated = True
            except Exception as e:
                print(f"❌ Failed to update ScanView.matcher: {e}")

        # Also update camera_service.matcher if present (for setups where matcher is attached to camera)
        if getattr(self, 'camera_service', None) and getattr(self.camera_service, 'matcher', None):
            try:
                self.camera_service.matcher.load_users_from_data(users_list)
                print("✅ Face Database Updated in CameraService.matcher")
                updated = True
            except Exception as e:
                print(f"❌ Failed to update CameraService.matcher: {e}")

        if not updated:
            print("⚠️ No matcher instance found to update. Ensure a FaceMatcher exists on ScanView or CameraService.")

    def on_pos_trigger(self, amount):
        print(f"⚡ Received POS Trigger: {amount} THB")
        self.current_bill_amount = amount
        
        current = self.stack.currentWidget()
        if current == self.view_home or current == self.view_no_result:
            self.start_scan_process()

    def on_scan_success(self, user_data_from_scan):
        """เมื่อสแกนหน้าเจอ"""
        user_id = user_data_from_scan.get("user_id") 
        role = user_data_from_scan.get("role", "user") # สมมติว่ามี field role

        print(f"🔍 Face Found: {user_id} (Role: {role})")

        # ✅ 1. เพิ่ม Logic เช็ค Admin (แก้บั๊กเด้งเองแล้วค้าง)
        if role == 'admin' or user_id == 'admin':
            print("👤 Admin Detected! Switching to Settings...")
            self.go_to_settings() # เรียกฟังก์ชันที่หยุดกล้องแล้ว
            return # จบการทำงาน ไม่ไปหน้า Confirm

        # ✅ 2. Logic ปกติสำหรับ User ทั่วไป
        # ดึงข้อมูลล่าสุดจาก DB (เพื่อความชัวร์เรื่องเงิน)
        fresh_user_data = self.db.get_user_by_id(user_id)
        
        if fresh_user_data:
            name = fresh_user_data.get("name", "Unknown")
            balance = float(fresh_user_data.get("balance", 0.0))
        else:
            name = user_data_from_scan.get("name", "Unknown")
            balance = float(user_data_from_scan.get("balance", 0.0))

        bill_to_pay = self.current_bill_amount if self.current_bill_amount > 0 else 100.0
        
        print(f"💰 Preparing Bill: {bill_to_pay} THB for {name}")
        
        self.view_confirm.set_user_data(user_id, name, balance, bill_to_pay)
        self.switch_to(self.view_confirm)

    def on_payment_complete(self, result):
        user_name = result['receipt']['user_name']
        new_balance = result['new_balance']
        
        self.current_bill_amount = 0.0
        
        self.view_success.set_payment_details(user_name, new_balance)
        self.switch_to(self.view_success)

    def on_language_changed(self, lang):
        print(f"Language changed to: {lang}")
        # ใส่ Logic เปลี่ยนภาษา UI ตรงนี้ (ถ้ามี)

    def keyPressEvent(self, event):
        # กด Q เพื่อออกโปรแกรม (Dev Mode)
        if event.key() == Qt.Key.Key_Q:
            print("👋 Quit command received (Q). Exiting...")
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        print("Closing Application...")
        if hasattr(self, 'camera_service'):
            self.camera_service.stop()
            self.camera_service.wait()
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()
        super().closeEvent(event)