import board
import busio
import supervisor
import time
import usb_cdc
import json

from kmk.kmk_keyboard import KMKKeyboard
from kmk.scanners.keypad import KeysScanner
from kmk.keys import KC
from kmk.modules.macros import Press, Release, Tap, Macros
from kmk.extensions.media_keys import MediaKeys
from adafruit_ssd1306 import SSD1306_I2C

keyboard = KMKKeyboard()
keyboard.extensions.append(MediaKeys())
keyboard.modules.append(Macros())

i2c = busio.I2C(board.D5, board.D4)
PINS = [board.D7, board.D8, board.D9, board.D10]

# Find I2C devices
while not i2c.try_lock():
    pass
devices = i2c.scan()
i2c.unlock()
print("I2C addresses found:", [hex(d) for d in devices])

# Display
displaySl = SSD1306_I2C(128, 32, i2c, addr=devices[0])

# Icons
play = [0xf3, 0xc3, 0x03, 0x03, 0xc3, 0xf3]
pause = [0x27, 0x27, 0x27, 0x27, 0x27, 0x27]

class display:
    showPaused = False
    showSkip = False
    showRewind = False
    def __init__(self):
        pass
    def clearDisplay():
        displaySl.fill(0)
        displaySl.show()
    def drawIcon(x, y, icon):
        for row in range(6):
            for col in range(8):
                if not icon[row] & (1 << col):
                    displaySl.pixel(x + col, y + row, 1)
    def displayMessage(message):
        displaySl.fill(0)
        displaySl.text(message, 0, 0, 1)
        displaySl.show()
    def displayData(volumeChange, isMuted, volume, title, artist, duration, position, playback_status):
        displaySl.fill(0)
        displaySl.text(title, 0, 0, 1)
        displaySl.text(artist, 0, 10, 1)

        # Progress Bar
        displaySl.hline(12, 26, 102, 1)
        displaySl.hline(12, 31, 102, 1)
        displaySl.vline(12, 26, 5, 1)
        displaySl.vline(113, 26, 5, 1)
        progressBarLength = int((position / duration) * 102)
        displaySl.fill_rect(12, 26, progressBarLength, 5, 1)

        # Progress Text
        secondsLeft = duration - position
        minutes = int(secondsLeft / 60)
        seconds = secondsLeft - (minutes * 60)
        displaySl.text(f"{minutes}:{seconds:02}", 12, 18, 1)

        # Icons
        if (playback_status == 4 and display.showPaused):
                display.showPaused = False
                display.drawIcon(106, 19, play)
        if (playback_status == 5):
            display.showPaused = True
            display.drawIcon(106, 19, pause)

        # Volume Bar
        if (volumeChange):
            volumeBarLength = int(volume / 4)
            if (isMuted == 1):
                volumeBarLength = 0
            displaySl.vline(127, 32 - volumeBarLength, volumeBarLength, 1)

        if (playback_status == 0 or playback_status == 1):
            display.displayMessage("No media playing")
            pass
        displaySl.show()

class Heartbeat:
    def __init__(self, interval=1.0):
        self._warned_no_data = False
        self.interval = interval
        self._next = 0

    def during_bootup(self, keyboard):
        display.displayMessage("Starting up...")
        pass
    
    def before_hid_send(self, keyboard):
        pass
    def after_hid_send(self, keyboard):
        pass
    def before_matrix_scan(self, keyboard):
        pass
    def after_matrix_scan(self, keyboard):
        connected = supervisor.runtime.usb_connected
        if (not connected):
            display.clearDisplay()
            return
        now = time.monotonic()
        if (usb_cdc.data.in_waiting > 0):
            data = json.loads(usb_cdc.data.readline().decode('utf-8').strip())
            print("Received:", data)
            if (data['isPlaying']):
                display.displayData(data['volumeChange'], data['muted'], data['volume'], data['title'], data['artist'], data['duration'], data['position'], data['playback_status'])
            else:
                display.displayMessage("No media playing")

        if now >= self._next:
            self._next = now + self.interval

keyboard.modules.append(Heartbeat(interval=1.0))

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