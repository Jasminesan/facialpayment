"""
ไฟล์นี้ถูกรวมเข้ากับแอปหลักแล้ว
เรียกใช้ผ่าน:  python src/main.py
แล้วกดปุ่ม "📝 ลงทะเบียน" หรือ "💰 เติมเงิน" บนหน้า Home

หรือจะรันไฟล์นี้โดยตรงก็ได้ — จะเปิดแอปหลักเหมือนกัน
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()