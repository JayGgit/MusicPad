import board
import busio
import time
import usb_cdc

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.macros import Press, Release, Tap, Macros
from kmk.extensions.media_keys import MediaKeys
from adafruit_ssd1306 import SSD1306_I2C

keyboard = KMKKeyboard()
keyboard.extensions.append(MediaKeys())
keyboard.modules.append(Macros())

i2c = busio.I2C(board.GP6, board.GP5)

PINS = [board.GP1, board.GP2, board.GP3, board.GP4]

# Find I2C devices
while not i2c.try_lock():
    pass
devices = i2c.scan()
i2c.unlock()
print("I2C addresses found:", [hex(d) for d in devices])

display = SSD1306_I2C(128, 32, i2c, addr=devices[0])
display.fill(0)
display.show()

# Tell kmk we are not using a key matrix
keyboard.matrix = KeysScanner(
    pins=PINS,
    value_when_pressed=False,
)

keyboard.keymap = [
    [KC.AUDIO_MUTE, KC.MEDIA_PREV_TRACK, KC.MEDIA_PLAY_PAUSE, KC.MEDIA_NEXT_TRACK]
]

# Start kmk!
if __name__ == '__main__':
    keyboard.go()