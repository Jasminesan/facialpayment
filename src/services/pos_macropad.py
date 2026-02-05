import time
import re
from PySide6.QtCore import QThread, Signal

# Note: pyserial is required. Install with `pip install pyserial`
import serial
import serial.tools.list_ports

class MacroPadListener(QThread):
    """Listener for MacroPad acting as USB-Serial POS emulator.

    This thread tries to open a serial device (configurable) and reads lines.
    Expected incoming line formats (examples):
      PAY:100.0\n
    or just a plain number:
      100.0\n
    Emits:
      payment_received(float)
    """

    payment_received = Signal(float)

    def __init__(self, port=None, baud=9600, auto_detect=True, poll_interval=1.0):
        super().__init__()
        self.port = port
        self.baud = baud
        self.auto_detect = auto_detect
        self.poll_interval = poll_interval
        self._running = True
        self.ser = None

    def run(self):
        print(f"📡 MacroPadListener starting (port={self.port}, baud={self.baud})")

        # If auto_detect requested and no explicit port, try to find a tty device
        if self.auto_detect and not self.port:
            self.port = self._auto_detect_port()
            if self.port:
                print(f"🔎 Auto-detected MacroPad on {self.port}")
            else:
                print("⚠️ No MacroPad serial device auto-detected. Will retry periodically.")

        while self._running:
            if not self.ser:
                if not self.port:
                    # try autodetect again (print candidate ports for debugging)
                    ports = list(serial.tools.list_ports.comports())
                    if ports:
                        print("🔍 Candidate serial ports:")
                        for p in ports:
                            print(f"  - {p.device} ({p.description})")
                    self.port = self._auto_detect_port()
                    if not self.port:
                        time.sleep(self.poll_interval)
                        continue
                    print(f"🔎 Auto-detected MacroPad on {self.port}")
                try:
                    self.ser = serial.Serial(self.port, self.baud, timeout=1)
                    print(f"✅ Opened serial {self.port} @ {self.baud}")
                except Exception as e:
                    print(f"❌ Failed to open serial {self.port}: {e}")
                    self.ser = None
                    # reset port if using auto-detect to retry later
                    if self.auto_detect:
                        self.port = None
                    time.sleep(self.poll_interval)
                    continue

            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"📩 Serial Received: {line}")
                    # Ignore obvious error/stacktrace lines, but allow lines that include a numeric token
                    low = line.lower()
                    if 'failed to send' in low or 'traceback' in low:
                        print("🔕 Ignoring REPL/debug/failed-send line from MacroPad")
                        continue
                    amount = self._parse_line(line)
                    if amount is not None:
                        try:
                            self.payment_received.emit(float(amount))
                        except Exception as e:
                            print(f"❌ Emit error: {e}")
            except Exception as e:
                print(f"❌ Serial read error: {e}")
                # close serial and try reopen
                try:
                    self.ser.close()
                except:
                    pass
                self.ser = None
                time.sleep(self.poll_interval)

        # cleanup
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
        print("📡 MacroPadListener stopped")

    def stop(self):
        self._running = False
        self.wait()

    def _parse_line(self, text):
        text = text.strip()
        if not text:
            return None
        if text.upper().startswith('PAY:'):
            val = text.split(':', 1)[1].strip()
        else:
            val = text

        # Try to extract the first numeric-looking token (allow commas/dots)
        m = re.search(r"[-+]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?|[-+]?\d+(?:[\.,]\d+)?", val)
        if not m:
            print(f"❌ Invalid amount format from MacroPad: {text}")
            return None

        num_str = m.group(0).replace(',', '.')
        try:
            return float(num_str)
        except ValueError:
            print(f"❌ Could not parse numeric amount from MacroPad token: {num_str}")
            return None

    def _auto_detect_port(self):
        # Look for typical USB serial devices (ttyACM*, ttyUSB*)
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            name = p.device
            desc = (p.description or '').lower()
            hwid = (p.hwid or '').lower()
            # heuristics: many MacroPads/USB devices show ACM or USB
            if 'usb' in desc or 'acm' in name or 'usb' in name or 'arduino' in desc or 'circuitpython' in desc:
                return name
        # fallback: return first ttyACM* or ttyUSB*
        for p in ports:
            if p.device and ('ttyACM' in p.device or 'ttyUSB' in p.device):
                return p.device
        return None
