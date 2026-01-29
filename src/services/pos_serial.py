import serial
from PySide6.QtCore import QThread, Signal
import time

class SerialListener(QThread):
    payment_received = Signal(float)

    def __init__(self, port='/dev/ttyUSB0', baud=9600):
        super().__init__()
        self.port = port
        self.baud = baud
        self.is_running = True
        self.ser = None

    def run(self):
        while self.is_running:
            try:
                if self.ser is None or not self.ser.is_open:
                    try:
                        self.ser = serial.Serial(self.port, self.baud, timeout=1)
                        print(f"✅ UART Listener Connected on {self.port}")
                    except Exception as e:
                        print(f"⏳ Waiting for Serial Device... ({e})")
                        time.sleep(2)
                        continue

                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line:
                        print(f"📥 Raw Data: {line}")
                        self._process_data(line)
                
                self.msleep(50) 

            except Exception as e:
                print(f"❌ Serial Error: {e}")
                if self.ser:
                    self.ser.close()
                time.sleep(1)

    def _process_data(self, data):
        if data.startswith("PAY:"):
            try:
                amount_str = data.split(":")[1]
                amount = float(amount_str)
                print(f"💰 Payment Request: {amount} THB")
                
                self.payment_received.emit(amount)
            except ValueError:
                print("❌ Invalid amount format")

    def stop(self):
        self.is_running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.wait()