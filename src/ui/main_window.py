from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Slot

from ui.ui_config import AppConfig

# Import Views
from ui.home_view import HomeView
from ui.scan_view import ScanView
from ui.confirm_view import ConfirmView
from ui.success_view import SuccessView
from ui.no_result_view import NoResultView
from ui.settings_view import SettingsView

# Import Services
from services.camera import CameraService
from database.connector import DatabaseHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biometric Payment System")
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_GRAY};")
        self.resize(700, 700)
        
        self.db = DatabaseHandler() 

        print("📷 Initializing Camera Service...")
        self.camera_service = CameraService()
        try:
            self.camera_service.start() 
            print("✅ Camera Started in Background!")
        except Exception as e:
            print(f"❌ Camera Init Error: {e}")

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

    def setup_connections(self):
        self.view_home.settings_clicked.connect(lambda: self.switch_to(self.view_settings))
        self.view_home.start_clicked.connect(self.start_scan_process)
        
        self.view_settings.back_clicked.connect(lambda: self.switch_to(self.view_home))
        self.view_settings.language_changed.connect(self.on_language_changed)

        self.view_scan.scanned_success.connect(self.on_scan_success)
        self.view_scan.scanned_fail.connect(lambda: self.switch_to(self.view_no_result))
        self.view_no_result.retry_clicked.connect(self.start_scan_process)

        self.view_confirm.payment_success.connect(self.on_payment_complete)
        self.view_confirm.cancel_clicked.connect(lambda: self.switch_to(self.view_home))
        self.view_success.finished.connect(lambda: self.switch_to(self.view_home))

    def switch_to(self, widget):
        self.stack.setCurrentWidget(widget)

    def start_scan_process(self):
        self.view_scan.start_scanning() 
        self.switch_to(self.view_scan)

    # ---------------------------------------------------------

    def on_scan_success(self, user_data_from_scan):
        user_id = user_data_from_scan.get("user_id") 
        
        print(f"🔍 Face Found: {user_id}. Fetching fresh data...")

        fresh_user_data = self.db.get_user_by_id(user_id)
        
        if fresh_user_data:
            name = fresh_user_data.get("name", "Unknown")
            balance = fresh_user_data.get("balance", 0.0)
        else:
            name = user_data_from_scan.get("name", "Unknown")
            balance = user_data_from_scan.get("balance", 0.0)

        current_bill_amount = 2000.0 
        
        self.view_confirm.set_user_data(user_id, name, balance, current_bill_amount)
        self.switch_to(self.view_confirm)

    def on_payment_complete(self, result):
        user_name = result['receipt']['user_name']
        new_balance = result['new_balance']
        self.view_success.set_payment_details(user_name, new_balance)
        self.switch_to(self.view_success)

    def on_language_changed(self, lang):
        print(f"Language changed to: {lang}")

    def closeEvent(self, event):
        print("Closing Application...")
        if hasattr(self, 'camera_service'):
            self.camera_service.stop()
        super().closeEvent(event)