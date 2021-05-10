# SPDX-FileCopyrightText: 2021 Dylan Herrada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_debouncer import Debouncer
import displayio
from adafruit_display_shapes.circle import Circle

# ESP32 SPI
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager

# Import NeoPixel Library
import neopixel

# Import Adafruit IO HTTP Client
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

group = displayio.Group()
# circle = Circle(240, 160, 150, fill=0x000000, outline=0xFFFFFF) # Titano
circle = Circle(160, 120, 100, fill=0x000000, outline=0xFFFFFF)  # Pynt
group.append(circle)
board.DISPLAY.show(group)
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# PyPortal ESP32 Setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
ADAFRUIT_IO_USER = secrets["aio_username"]
ADAFRUIT_IO_KEY = secrets["aio_key"]

# Create an instance of the Adafruit IO HTTP client
io = IO_HTTP(ADAFRUIT_IO_USER, ADAFRUIT_IO_KEY, wifi)

try:
    # Get the 'temperature' feed from Adafruit IO
    door_feed = io.get_feed("door")
except AdafruitIO_RequestError:
    door_feed = io.create_new_feed("door")

switch_pin = DigitalInOut(board.D3)
switch_pin.direction = Direction.INPUT
switch_pin.pull = Pull.UP
switch = Debouncer(switch_pin)


if switch.value == 0:
    group[0].fill = 0x00FF00
while True:
    try:
        switch.update()
        print(switch.state)
        if switch.rose:
            print("Door is open")
            io.send_data(door_feed["key"], 0)
            group[0].fill = 0xFF0000
            print("sent")

        if switch.fell:
            print("Door is closed")
            io.send_data(door_feed["key"], 1)
            group[0].fill = 0x00FF00
            print("sent")
    except (ValueError, RuntimeError) as err:
        print("Failed to get data, retrying\n", err)
        wifi.reset()
        continue
    time.sleep(1)
