import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QInputDialog, QLineEdit, QMessageBox
from PySide6.QtGui import QPainter, QPixmap, QFont
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from ui.ui_config import AppConfig, t


class HomeView(QWidget):
    # settings_requested(admin_mode: bool) -> True when long-press requested admin mode
    settings_requested = Signal(bool)
    start_clicked = Signal()        
    register_clicked = Signal()
    topup_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.bg_pixmap = None
        self._menu_visible = False
        # Timer for long-press on the hidden settings hotspot (5 seconds)
        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.setInterval(5000)
        self._hold_timer.timeout.connect(self._on_settings_hold)
        self.init_ui()

    def init_ui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "assets", "bg.jpg")

        if os.path.exists(image_path):
            self.bg_pixmap = QPixmap(image_path)
        else:
            self.setStyleSheet(f"background-color: {AppConfig.COLOR_BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 40)

        # Home should be only background image. We add a hidden settings hotspot
        # in the top-right that can be long-pressed for admin actions.
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_settings = QPushButton("")
        # Make the button invisible but still receive mouse events
        self.btn_settings.setFlat(True)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setFixedSize(70, 44)
        self.btn_settings.setStyleSheet("background: transparent; border: none;")
        top_bar.addWidget(self.btn_settings)
        layout.addLayout(top_bar)

        # keep spacing so other views align similarly
        layout.addStretch()

    # Any click on the home screen should open settings (non-admin).
    def mousePressEvent(self, event):
        # detect if press started on the hidden settings button
        child = self.childAt(event.pos())
        self._press_on_settings = (child is self.btn_settings)
        if getattr(self, '_press_on_settings', False):
            self._hold_timer.start()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # If the press started on the hidden settings hotspot and the hold timer
        # is still active, treat it as a short tap -> open settings (non-admin).
        if getattr(self, '_press_on_settings', False):
            if self._hold_timer.isActive():
                self._hold_timer.stop()
                self._press_on_settings = False
                # show PIN dialog to enter admin; on success emit admin request
                self._prompt_pin()
                return super().mouseReleaseEvent(event)
            # if timer already fired, _on_settings_hold has emitted admin=True
            self._press_on_settings = False
            return super().mouseReleaseEvent(event)

        # Otherwise, any tap on the background opens settings (non-admin)
        self.settings_requested.emit(False)
        return super().mouseReleaseEvent(event)

    # language updates are handled elsewhere; nothing to change here for home-only background
    def update_language(self):
        return

    def _prompt_pin(self):
        """Prompt for admin PIN. If correct, emit settings_requested(True)."""
        title = t("settings.title") if 't' in globals() else "Settings"
        prompt = "Enter admin PIN"
        pin, ok = QInputDialog.getText(self, title, prompt, QLineEdit.EchoMode.Password)
        if not ok:
            return
        if pin == AppConfig.ADMIN_PIN:
            self.settings_requested.emit(True)
        else:
            QMessageBox.warning(self, title, "PIN ไม่ถูกต้อง")

    def _on_settings_hold(self):
        # Called when the hidden settings button has been pressed for 5 seconds
        # -> request settings in admin mode
        self._press_on_settings = False
        self.settings_requested.emit(True)

    def paintEvent(self, event):
        if self.bg_pixmap:
            painter = QPainter(self)
            w, h = self.width(), self.height()
            pw, ph = self.bg_pixmap.width(), self.bg_pixmap.height()
            scale = max(w / pw, h / ph)
            nw, nh = int(pw * scale), int(ph * scale)
            x, y = (w - nw) // 2, (h - nh) // 2
            scaled = self.bg_pixmap.scaled(
                nw, nh,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(x, y, scaled)
        super().paintEvent(event)

    def showEvent(self, event):
        """Home shown - nothing special to hide here any more."""
        super().showEvent(event)