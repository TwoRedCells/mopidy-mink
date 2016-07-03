from __future__ import absolute_import, unicode_literals

import Adafruit_CharLCD
import logging
import socket
import threading
import time

log = logging.getLogger(__name__)

# Time a button must be held to count as a new button press.
DEBOUNCE_INTERVAL = 1.0


class LCD(object):
    red = (1.0, 0.0, 0.0)
    green = (0.0, 1.0, 0.0)
    blue = (0.0, 0.0, 1.0)
    yellow = (1.0, 1.0, 0.0)
    cyan = (0.0, 1.0, 1.0)
    magenta = (1.0, 0.0, 1.0)
    white = (1.0, 1.0, 1.0)
    colours = { "red" : red, "green" : green, "blue" : blue, "yellow" : yellow,
                "aqua" : cyan, "pink" : magenta, "white" : white }

    left = Adafruit_CharLCD.LEFT
    right = Adafruit_CharLCD.RIGHT
    up = Adafruit_CharLCD.UP
    down = Adafruit_CharLCD.DOWN
    select = Adafruit_CharLCD.SELECT
    buttons = [left, right, up, down, select]

    def __init__(self):
        self._stop = False
        self.pressed = None
        self.line1 = ""
        self.line2 = ""
        self.last_press_button = None
        self.last_press_time = time.time()

        # Initialize the LCD using the pins
        self.lcd = Adafruit_CharLCD.Adafruit_CharLCDPlate()

        # create some custom characters
        self.lcd.create_char(1, [2, 3, 2, 2, 14, 30, 12, 0])
        self.lcd.create_char(2, [0, 1, 3, 22, 28, 8, 0, 0])
        self.lcd.create_char(3, [0, 14, 21, 23, 17, 14, 0, 0])
        self.lcd.create_char(4, [31, 17, 10, 4, 10, 17, 31, 0])
        self.lcd.create_char(5, [8, 12, 10, 9, 10, 12, 8, 0])
        self.lcd.create_char(6, [2, 6, 10, 18, 10, 6, 2, 0])
        self.lcd.create_char(7, [31, 17, 21, 21, 21, 21, 17, 31])

    def start(self):
        ip = self.get_ip()
        log.info("IP is " + ip)
        self.lcd.clear()
        self.echo(1, "Mink")
        self.echo(2, ip if ip else "No internet")
        self.worker = threading.Thread(None, self.scan, "buttons thread")
        self.worker.start()

    def get_ip(self):
        """ Gets the IP address of the interface used to reach public sites. """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 0))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except socket.error:
            return None

    def colour(self, colour):
        value = LCD.colours[colour]
        self.lcd.set_color(value[0], value[1], value[2])

    def scan(self):
        while True:
            if self._stop:
                return
            for button in LCD.buttons:
                if self.lcd.is_pressed(button):
                    now = time.time()
                    if button != self.last_press_button or now - self.last_press_time > DEBOUNCE_INTERVAL:
                        self.last_press_time = now
                        self.last_press_button = button
                        self._on_pressed(button)
            time.sleep(0.1)

    def clear(self):
        self.lcd.clear()

    def cursor(self, column, row=1):
        if column is None:
#            self.lcd.show_cursor(False)
            self.lcd.blink(False)
        else:
            self.lcd.set_cursor(column, row-1)
#            self.lcd.show_cursor(True)
            self.lcd.blink(True)

    def echo(self, line, text):
        padded = text.ljust(16)[:16]
        if line == 1:
            self.line1 = padded
        elif line == 2:
            self.line2 = padded
        else:
            raise ValueError("'line' must be a value between 1 and 2.")
        self.update()

    def update(self):
        text = self.line1 + "\n" + self.line2
        self.lcd.home()
        self.lcd.message(text)

    def stop(self):
        self._stop = True

    def _on_pressed(self, button):
        if self.pressed:
            self.pressed(button)
