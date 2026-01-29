import socket
from PySide6.QtCore import QThread, Signal

class SocketListener(QThread):
    payment_received = Signal(float)

    def __init__(self):
        super().__init__()
        self.host = '0.0.0.0' # ฟังจากทุกเครื่อง
        self.port = 65432
        self.is_running = True

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"📡 Waiting for Payment on port {self.port}...")
            
            while self.is_running:
                conn, addr = s.accept() # รอรับการเชื่อมต่อ
                with conn:
                    data = conn.recv(1024)
                    if data:
                        text = data.decode().strip()
                        if text.startswith("PAY:"):
                            try:
                                amount = float(text.split(":")[1])
                                self.payment_received.emit(amount)
                            except ValueError: pass