import socket
from PySide6.QtCore import QThread, Signal

class SerialListener(QThread):
    # ชื่อ Signal ต้องเหมือนเดิมเพื่อให้ main_window รับได้
    payment_received = Signal(float)

    # รับ arguments หลอกๆ ไว้ (port, baud) เพื่อไม่ให้ main_window error ตอนส่งค่ามา
    def __init__(self, port='/dev/ttyUSB0', baud=9600):
        super().__init__()
        self.host = '0.0.0.0'  # ฟังจากทุก IP ในวง
        self.port = 65432      # Port ประตูบ้าน (ต้องตรงกับฝั่ง Mac)
        self.is_running = True
        self.server_socket = None

    def run(self):
        print(f"📡 Waiting for Wi-Fi Payment on Port {self.port}...")
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # แก้ปัญหา Address already in use
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()

            while self.is_running:
                try:
                    # รอการเชื่อมต่อ (Blocking)
                    conn, addr = self.server_socket.accept()
                    with conn:
                        print(f"🔗 Connected by {addr}")
                        data = conn.recv(1024)
                        if data:
                            text = data.decode('utf-8', errors='ignore').strip()
                            print(f"📩 Received: {text}")
                            
                            if text.startswith("PAY:"):
                                try:
                                    amount = float(text.split(":")[1])
                                    self.payment_received.emit(amount)
                                except ValueError:
                                    print("❌ Invalid Amount Format")
                except OSError:
                    # กรณี Socket ถูกปิด
                    break
                    
        except Exception as e:
            print(f"❌ Socket Error: {e}")
        finally:
            self.stop()

    def stop(self):
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.wait()