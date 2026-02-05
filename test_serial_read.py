#!/usr/bin/env python3
"""
Simple serial reader for debugging MacroPad output.
Usage:
    python test_serial_read.py /dev/ttyACM0 115200

Will print timestamp and repr of each received line.
"""
import sys
import time

try:
    import serial
except Exception:
    print("pyserial not installed. Install with: pip install pyserial")
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_serial_read.py <device> [baud]")
        sys.exit(1)

    port = sys.argv[1]
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f"Failed to open {port} : {e}")
        sys.exit(1)

    print(f"Listening on {port} @ {baud} - press Ctrl-C to exit")
    try:
        while True:
            line = ser.readline()
            if not line:
                continue
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            try:
                text = line.decode('utf-8', errors='replace').rstrip('\n')
            except Exception:
                text = repr(line)
            print(f"[{now}] GOT: {repr(text)}")
    except KeyboardInterrupt:
        print('\nExiting')
    finally:
        try:
            ser.close()
        except:
            pass

if __name__ == '__main__':
    main()
