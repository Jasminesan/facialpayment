import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer, QRectF, Slot
from PySide6.QtGui import QPainter, QPen, QColor, QImage, QPainterPath, QBrush, QPixmap
from ui.ui_config import AppConfig
from services.camera import CameraService
from database.connector import DatabaseHandler

class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(450, 450) 
        self.current_frame = None

    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def start_anim(self):
        self.angle = 0
        self.timer.start(30)

    def stop_anim(self):
        self.timer.stop()
        self.current_frame = None
        self.update()

    def set_frame(self, image: QImage):
        self.current_frame = image
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(10, 10, 430, 430)
        path = QPainterPath()
        path.addEllipse(rect)

        painter.save()
        painter.setClipPath(path)

        if self.current_frame:
            pixmap = QPixmap.fromImage(self.current_frame)
            scaled = pixmap.scaled(
                int(rect.width()), int(rect.height()),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            x = rect.x() + (rect.width() - scaled.width()) / 2
            y = rect.y() + (rect.height() - scaled.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            painter.fillPath(path, QBrush(QColor("#E0E0E0")))

        painter.restore()

        pen = QPen(QColor("#FFC107"))
        pen.setWidth(10)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect.toRect(), -self.angle * 16, -100 * 16)

# --- ScanView (เพิ่ม Logic Timeout) ---
class ScanView(QWidget):
    scanned_success = Signal(dict)
    scanned_fail = Signal()

    def __init__(self):
        super().__init__()
        self.db = DatabaseHandler()
        self.camera = None
        
        # ✅ เพิ่ม Timer สำหรับ Timeout
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True) # ทำงานครั้งเดียวแล้วหยุด
        self.timeout_timer.timeout.connect(self.on_scan_timeout) # ถ้าเวลาหมดให้เรียกฟังก์ชันนี้

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN};")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)

        self.lbl_status = QLabel("Scanning...")
        self.lbl_status.setStyleSheet("font-size: 28px; font-weight: bold; color: #333333; background-color: transparent;")

        self.loading_circle = LoadingWidget()

        layout.addWidget(self.lbl_status, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_circle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    def start_scanning(self):
        self.lbl_status.setText("Scanning...")
        self.loading_circle.start_anim()
        
        # เริ่มกล้อง
        if self.camera: self.camera.stop()
        self.camera = CameraService()
        self.camera.frame_received.connect(self.update_video)
        self.camera.face_detected.connect(self.check_face)
        self.camera.start()

        # ✅ เริ่มจับเวลา Timeout (เช่น 15 วินาที = 15000 ms)
        self.timeout_timer.start(15000)

    def stop_scanning(self):
        # ✅ หยุด Timer ด้วย เพื่อกันไม่ให้มันทำงานซ้อน
        self.timeout_timer.stop()

        if self.camera:
            self.camera.stop()
            self.camera.wait()
            self.camera = None
        self.loading_circle.stop_anim()

    def on_scan_timeout(self):
        """เมื่อหมดเวลาแล้วยังไม่เจอหน้า"""
        print("⏰ Scan Timeout! No face found.")
        self.stop_scanning()
        # ส่งสัญญาณ Fail เพื่อให้ Main Window เปลี่ยนไปหน้า No Result
        self.scanned_fail.emit()

    @Slot(QImage)
    def update_video(self, image):
        self.loading_circle.set_frame(image)

    @Slot(list)
    def check_face(self, vector):
        self.lbl_status.setText("Checking Database...")
        
        result = self.db.get_user_by_face(vector)
        
        if result and result['found']:
            self.stop_scanning()
            self.scanned_success.emit(result)
        else:
            pass 

    def hideEvent(self, event):
        self.stop_scanning()
        super().hideEvent(event)