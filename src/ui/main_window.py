from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import QMessageBox

from ui.ui_config import AppConfig, set_lang

# Import Views
from ui.home_view import HomeView
from ui.scan_view import ScanView
from ui.confirm_view import ConfirmView
from ui.success_view import SuccessView
from ui.no_result_view import NoResultView
from ui.settings_view import SettingsView
from ui.pin_view import PinView
from ui.settings_dev_view import SettingsDevView
from ui.register_view import RegisterView
from ui.topup_view import TopUpView
from ui.ui_config import t

# Import Services
from services.pos_macropad import MacroPadListener
from services.camera import CameraService
from database.connector import DatabaseHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ระบบชำระเงินด้วยใบหน้า")
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_GRAY};")
        
       
        self.showFullScreen() 
        
        self.db = DatabaseHandler() 
        self.current_bill_amount = 0.0
        self.pin_attempts = 0
        self.scan_mode = "payment"

        print("กำลังเริ่มกล้อง...")
        self.camera_service = CameraService()
        try:
            self.camera_service.start() 
            print("เริ่มกล้องสำเร็จ")
        except Exception as e:
            print(f"Camera Init Error: {e}")

        print("กำลังเชื่อมต่อฐานข้อมูลแบบ Realtime...")
        self._pending_face_users = None
        try:
            self.user_listener = self.db.listen_for_updates(self.update_face_database)
        except AttributeError:
            print("Warning: DatabaseHandler might not have 'listen_for_updates' yet.")

        # เริ่มระบบรับค่าจาก POS (MacroPad USB-Serial)
        try:
            self.serial_thread = MacroPadListener(port=None, baud=115200, auto_detect=True)
            self.serial_thread.payment_received.connect(self.on_pos_trigger)
            self.serial_thread.start()
            print("MacroPadListener (POS) เริ่มทำงาน")
        except Exception as e:
            print(f"MacroPad Init Error: {e}")

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
        self.view_pin = PinView()
        self.view_settings_dev = SettingsDevView()
        self.view_register = RegisterView(self.camera_service, self.db)
        self.view_topup = TopUpView(self.db)

        # Add Views to Stack
        self.stack.addWidget(self.view_home)       # 0
        self.stack.addWidget(self.view_scan)       # 1
        self.stack.addWidget(self.view_confirm)    # 2
        self.stack.addWidget(self.view_success)    # 3
        self.stack.addWidget(self.view_no_result)  # 4
        self.stack.addWidget(self.view_settings)   # 5
        self.stack.addWidget(self.view_pin)        # 6
        self.stack.addWidget(self.view_settings_dev)  # 7
        self.stack.addWidget(self.view_register)   # 8
        self.stack.addWidget(self.view_topup)      # 9

        self.setup_connections()
        self.stack.setCurrentWidget(self.view_home)

        # Apply current language to all views
        try:
            self._apply_language_to_all()
        except Exception:
            pass

        # If there was a pending face DB update before ScanView was created, apply it now
        if self._pending_face_users:
            try:
                if getattr(self.view_scan, 'matcher', None):
                    self.view_scan.matcher.load_users_from_data(self._pending_face_users)
                    print(f"Applied pending face DB ({len(self._pending_face_users)} users) to ScanView.matcher")
                self._pending_face_users = None
            except Exception as e:
                print(f"Failed to apply pending face DB to matcher: {e}")

    def setup_connections(self):
        # Home -> Settings / Register / TopUp
        # Home -> Settings (settings_requested(admin: bool))
        self.view_home.settings_requested.connect(self.go_to_settings)
        self.view_home.start_clicked.connect(self.start_scan_process)
        self.view_home.register_clicked.connect(self.go_to_register)
        self.view_home.topup_clicked.connect(self.go_to_topup)
        
        # Settings -> Home
        self.view_settings.back_clicked.connect(lambda: self.switch_to(self.view_home))
        self.view_settings.language_changed.connect(self.on_language_changed)
        self.view_settings.pin_clicked.connect(self.go_to_pin)

        # PIN -> Settings/Settings DEV/Home
        self.view_pin.back_clicked.connect(lambda: self.switch_to(self.view_settings))
        self.view_pin.pin_submitted.connect(self.on_pin_submitted)

        # Settings DEV -> Register / Topup / Settings
        self.view_settings_dev.register_clicked.connect(self.go_to_register)
        self.view_settings_dev.topup_clicked.connect(self.go_to_topup)
        self.view_settings_dev.back_clicked.connect(lambda: self.switch_to(self.view_settings))

        # Register -> Home
        self.view_register.back_clicked.connect(self.back_from_register)

        # TopUp -> Settings DEV
        self.view_topup.back_clicked.connect(lambda: self.switch_to(self.view_settings_dev))

        # Scan Logic
        self.view_scan.scanned_success.connect(self.on_scan_success)
        self.view_scan.scanned_fail.connect(lambda: self.switch_to(self.view_no_result))
        
        # Retry Logic
        self.view_no_result.retry_clicked.connect(self.retry_scan_based_on_mode)

        # Confirm & Payment Logic
        self.view_confirm.payment_success.connect(self.on_payment_complete)
        self.view_confirm.cancel_clicked.connect(lambda: self.switch_to(self.view_home))
        self.view_success.finished.connect(lambda: self.switch_to(self.view_home))

    def switch_to(self, widget):
        self.stack.setCurrentWidget(widget)

    # ========== Navigation ==========

    def go_to_settings(self, admin=False):
        print("เปิดหน้าตั้งค่า...")
        if hasattr(self.view_scan, 'stop_camera'):
             self.view_scan.stop_camera()
        self.switch_to(self.view_settings)

    def go_to_pin(self):
        self.view_pin.clear_pin()
        self.switch_to(self.view_pin)

    def on_pin_submitted(self, pin: str):
        if not pin:
            QMessageBox.warning(self, t("pin.title"), t("pin.err_empty"))
            return

        if pin == AppConfig.ADMIN_PIN:
            self.pin_attempts = 0
            self.view_pin.clear_pin()
            self.switch_to(self.view_settings_dev)
            return

        self.pin_attempts += 1
        self.view_pin.clear_pin()
        if self.pin_attempts > 5:
            self.pin_attempts = 0
            QMessageBox.warning(self, t("pin.title"), t("pin.err_limit"))
            self.switch_to(self.view_home)
            return

        QMessageBox.warning(self, t("pin.title"), t("pin.err_invalid"))

    def go_to_register(self):
        print("เปิดหน้าลงทะเบียน...")
        self.view_register.start_capture()
        self.switch_to(self.view_register)

    def back_from_register(self):
        self.view_register.stop_capture()
        self.switch_to(self.view_settings_dev)

    def go_to_topup(self):
        print("สแกนใบหน้าก่อนเข้าเติมเงิน...")
        self.view_topup.reset_view()
        self.start_scan_process(mode="topup")

    def start_scan_process(self, mode="payment"):
        self.scan_mode = mode
        timeout_ms = 3000 if mode == "topup" else 15000
        self.view_scan.start_scanning(timeout_ms=timeout_ms)
        self.switch_to(self.view_scan)

    def retry_scan_based_on_mode(self):
        if self.scan_mode == "topup":
            self.switch_to(self.view_settings_dev)
            return
        self.start_scan_process(self.scan_mode)

    # ========== Database ==========

    def update_face_database(self, users_list):
        print(f"อัพเดตฐานข้อมูลใบหน้า ({len(users_list)} คน)...")
        updated = False

        if hasattr(self, 'view_scan') and getattr(self.view_scan, 'matcher', None):
            try:
                self.view_scan.matcher.load_users_from_data(users_list)
                print("อัพเดตใน ScanView.matcher สำเร็จ")
                updated = True
            except Exception as e:
                print(f"Failed to update ScanView.matcher: {e}")

        if getattr(self, 'camera_service', None) and getattr(self.camera_service, 'matcher', None):
            try:
                self.camera_service.matcher.load_users_from_data(users_list)
                print("อัพเดตใน CameraService.matcher สำเร็จ")
                updated = True
            except Exception as e:
                print(f"Failed to update CameraService.matcher: {e}")

        if not updated:
            print("ไม่พบ matcher instance สำหรับอัพเดต")

    # ========== POS Trigger (ชำระเงิน — จาก POS เท่านั้น) ==========

    def on_pos_trigger(self, amount):
        print(f"ได้รับค่าจาก POS: {amount} บาท")
        self.current_bill_amount = amount
        
        current = self.stack.currentWidget()
        if current == self.view_home or current == self.view_no_result:
            self.start_scan_process()

    def on_scan_success(self, user_data_from_scan):
        """เมื่อสแกนหน้าเจอ"""
        user_id = user_data_from_scan.get("user_id") 
        role = user_data_from_scan.get("role", "user")

        print(f"พบใบหน้า: {user_id} (Role: {role})")

        if self.scan_mode == "topup":
            fresh_user_data = self.db.get_user_by_id(user_id)
            if fresh_user_data:
                self.view_topup.set_user(fresh_user_data)
                self.switch_to(self.view_topup)
            else:
                self.switch_to(self.view_no_result)
            return

        if role == 'admin' or user_id == 'admin':
            print("ตรวจพบ Admin! เปิดหน้าตั้งค่า...")
            self.go_to_settings()
            return

        fresh_user_data = self.db.get_user_by_id(user_id)
        
        if fresh_user_data:
            name = fresh_user_data.get("name", "ไม่ทราบ")
            balance = float(fresh_user_data.get("balance", 0.0))
        else:
            name = user_data_from_scan.get("name", "ไม่ทราบ")
            balance = float(user_data_from_scan.get("balance", 0.0))

        bill_to_pay = self.current_bill_amount if self.current_bill_amount > 0 else 100.0
        
        print(f"เตรียมบิล: {bill_to_pay} บาท สำหรับ {name}")
        
        self.view_confirm.set_user_data(user_id, name, balance, bill_to_pay)
        self.switch_to(self.view_confirm)

    def on_payment_complete(self, result):
        user_name = result['receipt']['user_name']
        new_balance = result['new_balance']
        
        self.current_bill_amount = 0.0
        
        self.view_success.set_payment_details(user_name, new_balance)
        self.switch_to(self.view_success)

    def on_language_changed(self, lang):
        print(f"เปลี่ยนภาษาเป็น: {lang}")
        try:
            set_lang(lang)
        except Exception:
            pass

        # propagate language change to every view that supports it
        self._apply_language_to_all()

        # update settings active button styles
        try:
            is_eng = (lang == "ENG")
            if hasattr(self.view_settings, 'update_btn_style'):
                self.view_settings.update_btn_style(self.view_settings.btn_eng, is_eng)
                self.view_settings.update_btn_style(self.view_settings.btn_tha, not is_eng)
        except Exception:
            pass

    def _apply_language_to_all(self):
        views = [
            self.view_home, self.view_scan, self.view_confirm,
            self.view_success, self.view_no_result, self.view_settings,
            self.view_pin, self.view_settings_dev,
            self.view_register, self.view_topup,
        ]
        for v in views:
            try:
                if hasattr(v, 'update_language'):
                    v.update_language()
            except Exception as e:
                print(f"Failed to update language on {v}: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Q:
            print("ออกจากโปรแกรม (Q)...")
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        print("กำลังปิดโปรแกรม...")
        # หยุด camera capture ของ register view ถ้ายังทำงานอยู่
        if hasattr(self, 'view_register'):
            self.view_register.stop_capture()
        if hasattr(self, 'camera_service'):
            self.camera_service.stop()
            self.camera_service.wait()
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()
        super().closeEvent(event)