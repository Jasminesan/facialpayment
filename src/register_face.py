import sys
import os
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QCheckBox, QHBoxLayout)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap

# ตั้งค่า Path ให้หาไฟล์ในโปรเจกต์เจอ
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))

from services.camera import CameraService
from database.connector import DatabaseHandler

class RegisterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Register New User (OAK-D PoE)")
        self.setGeometry(100, 100, 500, 750) 
        
        # Init Database & Camera
        self.db = DatabaseHandler()
        
        # ✅ แก้ไข: เรียกใช้ CameraService แบบมาตรฐาน (เหมือนหน้า Main)
        self.camera = CameraService() 
        
        self.current_vector = None
        self.is_capturing = True

        self.init_ui()
        self.setup_camera()

    def init_ui(self):
        layout = QVBoxLayout()

        # 1. Video Display
        self.video_label = QLabel("Waiting for OAK-D Camera...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(400, 300)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        layout.addWidget(self.video_label)

        # 2. Status Label
        self.status_label = QLabel("🔍 Looking for face...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: orange;")
        layout.addWidget(self.status_label)

        # 3. Input Fields
        # 3.1 User ID
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter User ID (e.g. 101)")
        layout.addWidget(self.id_input)

        # 3.2 Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Full Name")
        layout.addWidget(self.name_input)

        # 3.3 Balance
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("Initial Balance (e.g. 500.00)")
        layout.addWidget(self.balance_input)

        # 3.4 PDPA Consent
        self.pdpa_checkbox = QCheckBox("I agree to PDPA Consent (ยินยอมให้เก็บข้อมูลใบหน้า)")
        self.pdpa_checkbox.setStyleSheet("font-size: 14px; margin-top: 10px;")
        layout.addWidget(self.pdpa_checkbox)

        # 4. Buttons
        self.capture_btn = QPushButton("📸 FORCE CAPTURE")
        self.capture_btn.setStyleSheet("background-color: #f1c40f; font-weight: bold; padding: 10px;")
        self.capture_btn.clicked.connect(self.save_data)
        layout.addWidget(self.capture_btn)

        self.close_btn = QPushButton("❌ Close")
        self.close_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def setup_camera(self):
        # เชื่อมต่อ Signal จากกล้อง
        try:
            self.camera.frame_received.connect(self.update_frame)
            self.camera.face_detected.connect(self.update_vector)
            self.camera.start()
            print("✅ Register Camera Started")
        except Exception as e:
            QMessageBox.critical(self, "Camera Error", f"Could not start camera: {e}")

    @Slot(QImage)
    def update_frame(self, image):
        if self.is_capturing:
            pixmap = QPixmap.fromImage(image)
            # Scale ให้พอดีกับ Label
            self.video_label.setPixmap(pixmap.scaled(
                self.video_label.size(), 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))

    @Slot(list)
    def update_vector(self, vector):
        if self.is_capturing:
            self.current_vector = vector
            self.status_label.setText("✅ Face Detected! Ready to Save.")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")

    def save_data(self):
        # 1. ตรวจสอบข้อมูลนำเข้า (Validation)
        user_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        balance = self.balance_input.text().strip()
        pdpa_consent = self.pdpa_checkbox.isChecked()

        if not user_id or not name or not balance:
            QMessageBox.warning(self, "Error", "Please fill in all fields (ID, Name, Balance).")
            return

        if not pdpa_consent:
            QMessageBox.warning(self, "PDPA Required", "You must agree to PDPA consent to register.")
            return

        if self.current_vector is None:
            QMessageBox.warning(self, "No Face", "Camera hasn't detected a face yet.\nPlease wait for green status.")
            return

        # 2. บันทึกลง Database
        try:
            # ✅ แก้ไขจุดสำคัญ: ส่งแค่ 4 arguments ตามที่ DatabaseHandler รองรับ
            # (PDPA เช็คไปแล้วใน UI ไม่ต้องส่งเข้า DB หรือถ้าจะเก็บต้องไปแก้ DB เพิ่ม)
            success = self.db.register_user(user_id, name, balance, self.current_vector)
            
            if success:
                QMessageBox.information(self, "Success", f"User {name} (ID: {user_id}) registered successfully!")
                
                # เคลียร์ค่าหลังบันทึกเสร็จ
                self.name_input.clear()
                self.id_input.clear()
                self.balance_input.clear()
                self.pdpa_checkbox.setChecked(False)
                self.current_vector = None
                self.status_label.setText("🔍 Looking for face...")
                self.status_label.setStyleSheet("color: orange;")
            else:
                QMessageBox.critical(self, "Error", "Failed to save to database. Check terminal for details.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def closeEvent(self, event):
        print("Closing Register App...")
        if hasattr(self, 'camera'):
            self.camera.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegisterApp()
    window.show()
    sys.exit(app.exec())