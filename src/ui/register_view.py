import hashlib
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QFormLayout, QGroupBox,
    QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap, QFont, QDoubleValidator, QIntValidator

from ui.ui_config import AppConfig, t


class RegisterView(QWidget):
    """หน้าลงทะเบียนใบหน้า — ใช้กล้องจาก MainWindow (shared CameraService)"""

    back_clicked = Signal()

    def __init__(self, camera_service, db):
        super().__init__()
        self.camera = camera_service
        self.db = db
        self.current_vector = None
        self.is_capturing = False
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
        h_layout.addSpacing(60)  # balance the back button width

        root.addWidget(header)

        # ---- Scrollable content ----
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # -- กล้อง --
        cam_group = QGroupBox(t("reg.cam_group"))
        cam_group.setStyleSheet(self._group_style())
        cam_lay = QVBoxLayout(cam_group)

        self.video_label = QLabel(t("reg.cam_wait"))
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(280)
        self.video_label.setStyleSheet("background: #212121; color: #aaa; border-radius: 12px; font-size: 15px;")
        cam_lay.addWidget(self.video_label)

        self.status_label = QLabel(t("reg.searching"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800; padding: 4px;")
        cam_lay.addWidget(self.status_label)
        layout.addWidget(cam_group)

        # -- ฟอร์ม --
        form_group = QGroupBox(t("reg.form_group"))
        form_group.setStyleSheet(self._group_style())
        form = QFormLayout(form_group)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("เช่น 101, 102 ...")
        self.id_input.setValidator(QIntValidator(1, 999999))
        self.id_input.setStyleSheet(self._input_style())
        form.addRow(t("reg.uid"), self.id_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("ชื่อ - นามสกุล")
        self.name_input.setStyleSheet(self._input_style())
        form.addRow(t("reg.name"), self.name_input)

        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("เช่น 500.00")
        self.balance_input.setValidator(QDoubleValidator(0, 999999, 2))
        self.balance_input.setStyleSheet(self._input_style())
        form.addRow(t("reg.balance"), self.balance_input)

        layout.addWidget(form_group)

        # -- PDPA --
        pdpa_group = QGroupBox(t("reg.pdpa_group"))
        pdpa_group.setStyleSheet(self._group_style())
        pdpa_lay = QVBoxLayout(pdpa_group)

        pdpa_info = QLabel(t("reg.pdpa_info"))
        pdpa_info.setWordWrap(True)
        pdpa_info.setStyleSheet("color: #666; font-size: 13px; padding: 2px;")
        pdpa_lay.addWidget(pdpa_info)

        self.pdpa_checkbox = QCheckBox(t("reg.pdpa_check"))
        self.pdpa_checkbox.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 4px;")
        pdpa_lay.addWidget(self.pdpa_checkbox)
        layout.addWidget(pdpa_group)

        # -- ปุ่ม --
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self.btn_save = self._make_btn(t("reg.save"), "#4CAF50")
        self.btn_save.clicked.connect(self.save_data)
        btn_row.addWidget(self.btn_save)

        self.btn_clear = self._make_btn(t("reg.clear"), "#FF9800")
        self.btn_clear.clicked.connect(self.clear_form)
        btn_row.addWidget(self.btn_clear)

        layout.addLayout(btn_row)
        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def update_language(self):
        self.btn_back.setText(t("reg.back"))
        # header title
        # cam / form labels
        self.video_label.setText(t("reg.cam_wait"))
        self.status_label.setText(t("reg.searching"))
        # form labels are created using t() initially so they will show correctly

    # ================================================================
    # Camera connect / disconnect
    # ================================================================
    def start_capture(self):
        """เรียกตอนเข้าหน้านี้"""
        self.is_capturing = True
        self.current_vector = None
        self.status_label.setText(t("reg.searching"))
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800; padding: 4px;")
        try:
            self.camera.frame_received.connect(self.update_frame)
            self.camera.face_detected.connect(self.update_vector)
        except Exception:
            pass

    def stop_capture(self):
        """เรียกตอนออกจากหน้านี้"""
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
        if not self.is_capturing:
            return
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(
            pixmap.scaled(self.video_label.width(), self.video_label.height(),
                          Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    @Slot(list)
    def update_vector(self, vector):
        if not self.is_capturing:
            return
        self.current_vector = vector
        self.status_label.setText("✅  ตรวจพบใบหน้าแล้ว — พร้อมบันทึก")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E7D32; padding: 4px;")

    # ================================================================
    # Save
    # ================================================================
    @staticmethod
    def _hash_vector(vector) -> str:
        raw = ",".join(f"{v:.6f}" for v in vector)
        return hashlib.sha256(raw.encode()).hexdigest()

    def save_data(self):
        uid = self.id_input.text().strip()
        name = self.name_input.text().strip()
        balance = self.balance_input.text().strip()

        if not uid:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกรหัสผู้ใช้")
            self.id_input.setFocus(); return
        if not name:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกชื่อ-นามสกุล")
            self.name_input.setFocus(); return
        if not balance:
            QMessageBox.warning(self, "ข้อมูลไม่ครบ", "กรุณากรอกยอดเงินเริ่มต้น")
            self.balance_input.setFocus(); return
        if not self.pdpa_checkbox.isChecked():
            QMessageBox.warning(self, "ต้องยินยอม PDPA", "กรุณายินยอมให้จัดเก็บข้อมูลใบหน้าก่อน")
            return
        if self.current_vector is None:
            QMessageBox.warning(self, "ไม่พบใบหน้า", "กล้องยังไม่พบใบหน้า กรุณารอสถานะเป็นสีเขียว")
            return

        reply = QMessageBox.question(
            self, "ยืนยันการลงทะเบียน",
            f"ลงทะเบียน \"{name}\" (ID: {uid}) ใช่หรือไม่?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            vec_hash = self._hash_vector(self.current_vector)
            ok = self.db.register_user(uid, name, balance, self.current_vector, True)
            if ok:
                print(f"🔐 Face vector hash: {vec_hash[:16]}...")
                QMessageBox.information(self, "สำเร็จ", f"ลงทะเบียน \"{name}\" (ID: {uid}) เรียบร้อย!")
                self.clear_form()
            else:
                QMessageBox.critical(self, "ผิดพลาด", "บันทึกลงฐานข้อมูลไม่สำเร็จ")
        except Exception as e:
            QMessageBox.critical(self, "ผิดพลาด", str(e))

    def clear_form(self):
        self.id_input.clear()
        self.name_input.clear()
        self.balance_input.clear()
        self.pdpa_checkbox.setChecked(False)
        self.current_vector = None
        self.status_label.setText("🔍  กำลังค้นหาใบหน้า...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF9800; padding: 4px;")

    def _on_back(self):
        self.stop_capture()
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
    def _input_style():
        return """
            QLineEdit {
                border: 2px solid #e0e0e0; border-radius: 8px;
                padding: 10px 14px; font-size: 15px; background: #fafafa;
            }
            QLineEdit:focus { border-color: #4CAF50; background: white; }
        """

    @staticmethod
    def _make_btn(text, color):
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
            QPushButton:disabled {{ background-color: #bdbdbd; }}
        """)
        return btn
