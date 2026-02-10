import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer, QRectF, Slot
from PySide6.QtGui import QPainter, QPen, QColor, QImage, QPainterPath, QBrush, QPixmap

from ui.ui_config import AppConfig, t
from database.connector import DatabaseHandler
from services.face_matcher import FaceMatcher 

class LoadingWidget(QWidget):
    """Widget วงกลมหมุนๆ (เหมือนเดิม)"""
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

class ScanView(QWidget):
    scanned_success = Signal(dict)
    scanned_fail = Signal()

    def __init__(self, camera_service):
        super().__init__()
        self.db = DatabaseHandler()
        self.matcher = FaceMatcher(self.db) 
        self.camera = camera_service 
        self.is_scanning = False 

        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True) 
        self.timeout_timer.timeout.connect(self.on_scan_timeout) 
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN};")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15) # ลดช่องว่างลงหน่อย

        # 1. ข้อความสถานะหลัก
        self.lbl_status = QLabel(t("scan.waiting"))
        self.lbl_status.setStyleSheet("font-size: 28px; font-weight: bold; color: #333333;")

        # 2. วงกลมกล้อง
        self.loading_circle = LoadingWidget()

        # 3. ✅ [เพิ่มใหม่] ข้อความแนะนำ (Hint) ตัวสีแดงๆ ส้มๆ
        self.lbl_hint = QLabel("") 
        self.lbl_hint.setStyleSheet("font-size: 22px; font-weight: bold; color: #FF5722;")
        self.lbl_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_status, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_circle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_hint, alignment=Qt.AlignmentFlag.AlignCenter) # ใส่ไว้ใต้กล้อง
        
        self.setLayout(layout)
    
    

    def start_scanning(self):
        self.lbl_status.setText(t("scan.scanning"))
        self.lbl_hint.setText(t("scan.look_camera"))
        self.loading_circle.start_anim()
        self.is_scanning = True 

        try:
            try: self.camera.frame_received.disconnect(self.update_video)
            except: pass
            try: self.camera.face_detected.disconnect(self.check_face)
            except: pass

            self.camera.frame_received.connect(self.update_video)
            self.camera.face_detected.connect(self.check_face)
        except Exception as e:
            print(f"Connection Error: {e}")

        self.timeout_timer.start(15000)

    def stop_scanning(self):
        self.is_scanning = False 
        self.timeout_timer.stop()
        if hasattr(self, 'loading_circle'):
            self.loading_circle.stop_anim()
            
        self.lbl_hint.setText("") # เคลียร์ข้อความเมื่อหยุด

        try:
            self.camera.frame_received.disconnect(self.update_video)
        except: pass 
        try:
            self.camera.face_detected.disconnect(self.check_face)
        except: pass

    def on_scan_timeout(self):
        if not self.is_scanning: return
        self.stop_scanning()
        self.scanned_fail.emit()

    @Slot(QImage)
    def update_video(self, image):
        if not self.is_scanning: return
        if hasattr(self, 'loading_circle'):
            self.loading_circle.set_frame(image)

    @Slot(list)
    def check_face(self, vector):
        if not self.is_scanning: return

        self.lbl_status.setText(t("scan.checking"))
        
        result = self.matcher.find_match(vector) 

        if result:
            score = result.get('similarity', 0)
            print(f"Similarity: {score:.2f}")

            if result['found']:
                self.lbl_hint.setStyleSheet("color: green;")
                self.lbl_hint.setText(t("scan.success"))
                self.stop_scanning()
                self.scanned_success.emit(result)
            else:
                self.lbl_hint.setStyleSheet("color: #FF5722;") # สีส้ม
                if score > 0.35: 
                    self.lbl_hint.setText(t("scan.move_closer"))
                elif score > 0.1:
                    self.lbl_hint.setText(t("scan.come_closer"))
                else:
                    self.lbl_hint.setText(t("scan.not_clear"))
        else:
            self.lbl_hint.setText(t("scan.no_match"))

    def update_language(self):
        self.lbl_status.setText(t("scan.waiting"))