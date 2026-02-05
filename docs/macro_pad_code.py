# code.py (CircuitPython) - MacroPad RP2040 (queue + retry for usb_cdc.data)
# Copy this to CIRCUITPY/code.py on your MacroPad

import time
import usb_cdc
import board
import displayio
import terminalio
import keypad
import neopixel
from adafruit_display_text import label

# --- Hardware setup ---
KEY_PINS = (
    board.KEY1, board.KEY2, board.KEY3,
    board.KEY4, board.KEY5, board.KEY6,
    board.KEY7, board.KEY8, board.KEY9,
    board.KEY10, board.KEY11, board.KEY12
)

keys = keypad.Keys(KEY_PINS, value_when_pressed=False, pull=True)
pixels = neopixel.NeoPixel(board.NEOPIXEL, 12)
pixels.brightness = 0.25

KEY_MAP = {
    0: '7', 1: '8', 2: '9',
    3: '4', 4: '5', 5: '6',
    6: '1', 7: '2', 8: '3',
    9: 'DEL', 10: '0', 11: 'ENTER'
}

# Display (optional)
display = board.DISPLAY
main_group = displayio.Group()
total_label = label.Label(terminalio.FONT, text="TOTAL: 0", scale=2, x=5, y=15, color=0x00FF00)
input_label = label.Label(terminalio.FONT, text="0", scale=3, x=5, y=45, color=0xFFFFFF)
main_group.append(total_label)
main_group.append(input_label)
display.root_group = main_group

current_input = ""
total_sum = 0

# --- Outgoing queue & send logic ---
outgoing = []        # list of bytes messages waiting to be sent
last_flush = 0
FLUSH_INTERVAL = 0.15  # seconds


def update_display():
    input_label.text = current_input if current_input != "" else "0"
    total_label.text = f"TOTAL: {total_sum}"


def set_leds():
    pixels.fill((0, 0, 0))
    for i in range(9):
        pixels[i] = (20, 20, 20)
    pixels[10] = (20, 20, 20)
    pixels[9] = (100, 0, 0)
    pixels[11] = (0, 100, 0)

set_leds()


def queue_pay(amount):
    msg = f"PAY:{amount:.2f}\n".encode('utf-8')
    outgoing.append(msg)
    flash_led(11, (0,200,0), 0.06)  # show enter flash
    try_flush_queue()  # try immediately


def try_flush_queue():
    global outgoing
    usb_data = getattr(usb_cdc, 'data', None)
    if usb_data is None:
        return
    connected = getattr(usb_data, 'connected', None)
    if connected is False:
        return
    while outgoing:
        msg = outgoing[0]
        try:
            usb_data.write(msg)
            outgoing.pop(0)
            flash_led(11, (0,255,0), 0.06)
            time.sleep(0.02)
        except Exception as e:
            try:
                usb_cdc.console.write(("DEBUG: send error: %s\n" % str(e)).encode('utf-8'))
            except Exception:
                pass
            break


def flash_led(idx, color, duration=0.08):
    prev = pixels[idx]
    pixels[idx] = color
    time.sleep(duration)
    set_leds()

# --- main loop ---
while True:
    now = time.monotonic()
    if now - last_flush > FLUSH_INTERVAL:
        try_flush_queue()
        last_flush = now

    event = keys.events.get()
    if event:
        key_num = event.key_number
        if event.pressed:
            pixels[key_num] = (255, 255, 255)
            val = KEY_MAP[key_num]

            if val in '0123456789':
                if len(current_input) < 8:
                    current_input += val

            elif val == 'DEL':
                if len(current_input) > 0:
                    current_input = current_input[:-1]
                else:
                    total_sum = 0
                    total_label.color = 0xFF0000
                    pixels.fill((255, 0, 0))
                    time.sleep(0.12)
                    set_leds()

            elif val == 'ENTER':
                if current_input != "":
                    try:
                        amount = int(current_input)
                    except Exception:
                        amount = 0
                    queue_pay(amount)
                    total_sum += amount
                    current_input = ""
                    total_label.color = 0x00FF00

            update_display()

        elif event.released:
            set_leds()

    time.sleep(0.01)
