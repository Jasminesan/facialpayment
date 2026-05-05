import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGroupBox, QScrollArea,
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QImage, QPixmap, QFont

from ui.ui_config import AppConfig, t


class RegisterView(QWidget):
    """หน้าลงทะเบียนใบหน้า — ป้อน UID แล้วสแกนใบหน้า"""

    back_clicked = Signal()
    registration_complete = Signal(dict)  # {"user_id": ..., "name": ..., "face_vector": ...}

    def __init__(self, camera_service, db):
        super().__init__()
        self.camera = camera_service
        self.db = db
        self.current_vector = None
        self.is_capturing = False
        self.current_uid = None
        self.current_user = None
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
        header.setStyleSheet("background-color: #4CAF50;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)

        self.btn_back = QPushButton(t("reg.back"))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        self.btn_back.clicked.connect(self._on_back)
        h_layout.addWidget(self.btn_back)

        lbl_title = QLabel(t("reg.title"))
        lbl_title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; background: transparent;")
        lbl_title.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(lbl_title, 1)
        h_layout.addSpacing(60)

        root.addWidget(header)

        # ---- Main Container ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # === Page 1: UID Input Keypad ===
        self.page_uid = QWidget()
        uid_layout = QVBoxLayout(self.page_uid)
        uid_layout.setContentsMargins(0, 0, 0, 0)
        uid_layout.setSpacing(20)

        # Description
        desc = QLabel("กรุณากรอกรหัสผู้ใช้ (UID)")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        uid_layout.addWidget(desc)

        # UID Display
        self.uid_display = QLabel("_____")
        self.uid_display.setAlignment(Qt.AlignCenter)
        self.uid_display.setStyleSheet("""
            QLabel {
                font-size: 48px; font-weight: bold; color: #4CAF50;
                background: #f5f5f5; border: 3px solid #e0e0e0;
                border-radius: 10px; padding: 20px;
                font-family: monospace;
            }
        """)
        uid_layout.addWidget(self.uid_display)

        # Keypad (1-9, 0, DEL, OK)
        keypad_layout = QVBoxLayout()
        keypad_layout.setSpacing(10)

        # Row 1-3: Numbers
        for row_num in range(3):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)
            for col in range(3):
                num = (row_num * 3) + col + 1
                btn = self._make_keypad_btn(str(num))
                btn.clicked.connect(lambda checked, n=num: self._on_uid_key(n))
                row_layout.addWidget(btn)
            keypad_layout.addLayout(row_layout)

        # Row 4: 0, DEL, OK
        row4_layout = QHBoxLayout()
        row4_layout.setSpacing(10)

        btn_0 = self._make_keypad_btn("0")
        btn_0.clicked.connect(lambda: self._on_uid_key(0))
        row4_layout.addWidget(btn_0)

        btn_del = self._make_keypad_btn("DEL", "#FF9800")
        btn_del.clicked.connect(self._on_uid_delete)
        row4_layout.addWidget(btn_del)

        btn_ok = self._make_keypad_btn("OK", "#4CAF50")
        btn_ok.clicked.connect(self._on_uid_submit)
        row4_layout.addWidget(btn_ok)

        keypad_layout.addLayout(row4_layout)
        uid_layout.addLayout(keypad_layout)
        uid_layout.addStretch()

        # === Page 2: Confirmation ===
        self.page_confirm = QWidget()
        confirm_layout = QVBoxLayout(self.page_confirm)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(20)

        # User Info
        info_group = QGroupBox("ยืนยันข้อมูล")
        info_group.setStyleSheet(self._group_style())
        info_lay = QVBoxLayout(info_group)

        self.confirm_uid = QLabel()
        self.confirm_uid.setStyleSheet("font-size: 15px; color: #333;")
        info_lay.addWidget(self.confirm_uid)

        self.confirm_name = QLabel()
        self.confirm_name.setStyleSheet("font-size: 15px; color: #333;")
        info_lay.addWidget(self.confirm_name)

        self.confirm_balance = QLabel()
        self.confirm_balance.setStyleSheet("font-size: 15px; color: #333;")
        info_lay.addWidget(self.confirm_balance)

        confirm_layout.addWidget(info_group)

        # Scanning Area
        scan_group = QGroupBox("สแกนใบหน้า")
        scan_group.setStyleSheet(self._group_style())
        scan_lay = QVBoxLayout(scan_group)

        self.scan_video = QLabel("กำลังเชื่อมต่อกล้อง...")
        self.scan_video.setAlignment(Qt.AlignCenter)
        self.scan_video.setMinimumHeight(250)
        self.scan_video.setStyleSheet("background: #212121; color: #aaa; border-radius: 10px; font-size: 14px;")
        scan_lay.addWidget(self.scan_video)

        self.scan_status = QLabel("กำลังค้นหาใบหน้า...")
        self.scan_status.setAlignment(Qt.AlignCenter)
        self.scan_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
        scan_lay.addWidget(self.scan_status)

        confirm_layout.addWidget(scan_group)
        confirm_layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_back_confirm = self._make_btn("กลับ", "#FF9800")
        btn_back_confirm.clicked.connect(self._on_back_to_uid)
        btn_layout.addWidget(btn_back_confirm)

        confirm_layout.addLayout(btn_layout)

        # Add pages to layout
        layout.addWidget(self.page_uid)
        layout.addWidget(self.page_confirm)
        self.page_confirm.hide()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def update_language(self):
        self.btn_back.setText(t("reg.back"))

    # ================================================================
    # UID Input Handlers
    # ================================================================
    def _on_uid_key(self, num):
        """เพิ่มตัวเลขเข้า UID"""
        if len(self.current_uid) < 6:
            self.current_uid += str(num)
            self._update_uid_display()

    def _on_uid_delete(self):
        """ลบตัวเลขสุดท้าย"""
        if len(self.current_uid) > 0:
            self.current_uid = self.current_uid[:-1]
            self._update_uid_display()

    def _update_uid_display(self):
        """อัปเดตการแสดง UID"""
        if len(self.current_uid) == 0:
            self.uid_display.setText("_____")
        else:
            self.uid_display.setText(self.current_uid)

    def _on_uid_submit(self):
        """ตรวจสอบ UID จาก DB"""
        if len(self.current_uid) == 0:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอก UID")
            return

        try:
            # ค้นหา user ด้วย UID
            user = self.db.get_user_by_id(self.current_uid)
            if not user:
                QMessageBox.warning(self, "ไม่พบ UID", f"ไม่พบ UID: {self.current_uid} ในระบบ")
                self._clear_uid_input()
                return

            # เจอแล้ว - แสดง confirmation page
            self.current_user = user
            self._show_confirmation_page()

        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", str(e))

    def _clear_uid_input(self):
        """ล้าง UID input"""
        self.current_uid = ""
        self._update_uid_display()

    # ================================================================
    # Confirmation Page
    # ================================================================
    def _show_confirmation_page(self):
        """แสดง confirmation page กับ camera scan"""
        # ซ่อน UID page แสดง confirm page
        self.page_uid.hide()
        self.page_confirm.show()

        # แสดงข้อมูล
        self.confirm_uid.setText(f"รหัส (UID): {self.current_user.get('user_id', 'N/A')}")
        self.confirm_name.setText(f"ชื่อ: {self.current_user.get('name', 'N/A')}")
        self.confirm_balance.setText(f"ยอดเงิน: {self.current_user.get('balance', 0):.2f} บาท")

        # เริ่มสแกนใบหน้า
        self.start_capture()

    def _on_back_to_uid(self):
        """กลับไปหน้า UID input"""
        self.stop_capture()
        self.page_confirm.hide()
        self.page_uid.show()
        self._clear_uid_input()

    # ================================================================
    # Camera Capture & Face Detection
    # ================================================================
    def start_capture(self):
        """เรียกเมื่อเข้าหน้า confirmation"""
        self.is_capturing = True
        self.current_vector = None
        self.scan_status.setText("กำลังค้นหาใบหน้า...")
        self.scan_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        try:
            self.camera.frame_received.connect(self.update_frame)
            self.camera.face_detected.connect(self.update_vector)
        except Exception:
            pass

    def stop_capture(self):
        """เรียกเมื่อออกจากหน้า"""
        self.is_capturing = False
        try:
            self.camera.frame_received.disconnect(self.update_frame)
        except Exception:
            pass
        try:
            self.camera.face_detected.disconnect(self.update_vector)
        except Exception:
            pass

    @Slot(QImage)
    def update_frame(self, image):
        if not self.is_capturing or not self.page_confirm.isVisible():
            return
        pixmap = QPixmap.fromImage(image)
        self.scan_video.setPixmap(
            pixmap.scaled(self.scan_video.width(), self.scan_video.height(),
                          Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    @Slot(list)
    def update_vector(self, vector):
        if not self.is_capturing or not self.page_confirm.isVisible():
            return

        self.current_vector = vector
        self.scan_status.setText("ตรวจพบใบหน้า ✓ กำลังบันทึก...")
        self.scan_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32;")

        # บันทึกลง DB
        self._save_registration()

    def _save_registration(self):
        """บันทึกข้อมูลลงฐานข้อมูล"""
        try:
            if not self.current_user or not self.current_vector:
                return

            user_id = self.current_user.get("user_id")
            name = self.current_user.get("name")
            balance = self.current_user.get("balance", 0)

            # อัพเดต user document ด้วย face vector
            ok = self.db.register_user(
                user_id, name, balance,
                self.current_vector,
                pdpa_consent=True, role="user"
            )

            if ok:
                self.scan_status.setText("ลงทะเบียนสำเร็จ ✓")
                self.scan_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E7D32;")

                # ส่ง signal
                registration_data = {
                    "user_id": user_id,
                    "name": name,
                    "balance": balance,
                    "face_vector": self.current_vector
                }
                self.registration_complete.emit(registration_data)

                # หน่วงเวลา 2 วินาที แล้วกลับ HOME
                QTimer.singleShot(2000, self._reset_to_home)
            else:
                self.scan_status.setText("บันทึกล้มเหลว ❌")
                self.scan_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
                QMessageBox.critical(self, "ข้อผิดพลาด", "บันทึกลงฐานข้อมูลไม่สำเร็จ")

        except Exception as e:
            self.scan_status.setText(f"เกิดข้อผิดพลาด ❌")
            self.scan_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
            QMessageBox.critical(self, "ข้อผิดพลาด", str(e))

    def _reset_to_home(self):
        """รีเซ็ตกลับหน้า UID input และออก"""
        self.stop_capture()
        self._clear_uid_input()
        self.page_confirm.hide()
        self.page_uid.show()
        self.current_user = None
        self.back_clicked.emit()

    def _on_back(self):
        """กลับหน้าแรก"""
        self.stop_capture()
        self._clear_uid_input()
        self.page_confirm.hide()
        self.page_uid.show()
        self.back_clicked.emit()

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
    def _make_keypad_btn(text, color="#4CAF50"):
        """สร้างปุ่ม keypad"""
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: white;
                font-weight: bold; font-size: 18px;
                border-radius: 8px; border: none;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton:pressed {{ opacity: 0.7; }}
        """)
        return btn

    @staticmethod
    def _make_btn(text, color):
        """สร้างปุ่มทั่วไป"""
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(48)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; color: white;
                font-weight: bold; font-size: 16px;
                border-radius: 10px; border: none; padding: 8px 16px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        return btn

