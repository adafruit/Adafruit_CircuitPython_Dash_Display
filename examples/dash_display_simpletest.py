# SPDX-FileCopyrightText: 2021 Dylan Herrada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import ssl
import displayio
import board
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_text.label import Label
import terminalio
import touchio
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT
from adafruit_dash_display import Hub

up = DigitalInOut(board.BUTTON_UP)
up.direction = Direction.INPUT
up.pull = Pull.DOWN

select = DigitalInOut(board.BUTTON_SELECT)
select.direction = Direction.INPUT
select.pull = Pull.DOWN

down = DigitalInOut(board.BUTTON_DOWN)
down.direction = Direction.INPUT
down.pull = Pull.DOWN

back = touchio.TouchIn(board.CAP7)
submit = touchio.TouchIn(board.CAP8)

lamp = None

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise


def rgb_set_color(label, message, index):
    label.color = int(message[1:], 16)


rgb_group = displayio.Group(max_size=9)
R_label = Label(
    terminalio.FONT,
    text="   +\nR:\n   -",
    color=0xFFFFFF,
    anchor_point=((0, 0.5)),
    anchored_position=((5, 120)),
    scale=2,
)
G_label = Label(
    terminalio.FONT,
    text="   +\nG:\n   -",
    color=0xFFFFFF,
    anchor_point=((0, 0.5)),
    anchored_position=((90, 120)),
    scale=2,
)
B_label = Label(
    terminalio.FONT,
    text="   +\nB:\n   -",
    color=0xFFFFFF,
    anchor_point=((0, 0.5)),
    anchored_position=((175, 120)),
    scale=2,
)
rgb_group.append(R_label)
rgb_group.append(G_label)
rgb_group.append(B_label)
R = Label(
    terminalio.FONT,
    text="00",
    color=0xFFFFFF,
    anchor_point=((0, 0.5)),
    anchored_position=((35, 120)),
    scale=2,
)
G = Label(
    terminalio.FONT,
    text="00",
    color=0xFFFFFF,
    anchor_point=((0, 0.5)),
    anchored_position=((120, 120)),
    scale=2,
)
B = Label(
    terminalio.FONT,
    text="00",
    color=0xFFFFFF,
    anchor_point=((0, 0.5)),
    anchored_position=((205, 120)),
    scale=2,
)
rgb_group.append(R)
rgb_group.append(G)
rgb_group.append(B)

# pylint: disable=unused-argument


def on_temperature(client, feed_id, message):
    funhouse.set_text(f"Temperature: {float(message):.1f} C", 1)


def on_neopixel(client, feed_id, message):
    funhouse.set_text(f"LED: {message}", 3)
    funhouse.set_text_color(int(message[1:], 16), 3)


def on_battery(client, feed_id, message):
    funhouse.set_text(f"Battery: {message}%", 4)
    if int(message) <= 20:
        funhouse.set_text_color(0xFF0000, 4)
    else:
        funhouse.set_text_color(0x00FF00, 4)


def on_door(client, feed_id, message):
    if int(message):
        funhouse.set_text("Door closed", 5)
        funhouse.set_text_color(0x00FF00, 5)
    else:
        funhouse.set_text("Door open", 5)
        funhouse.set_text_color(0xFF0000, 5)


def rgb(last):
    display.show(None)
    time.sleep(0.5)
    display.show(rgb_group)
    time.sleep(0.5)
    index = 0
    colors = [00, 00, 00]

    while True:
        if select:
            index += 1
            if index == 3:
                index = 0
            time.sleep(0.3)
            continue

        if up:
            colors[index] += 1
            if colors[index] == 256:
                colors[index] = 0
            rgb_group[index + 3].text = hex(colors[index])[2:]
            time.sleep(0.01)
            continue

        if down:
            colors[index] -= 1
            if colors[index] == -1:
                colors[index] = 255
            rgb_group[index + 3].text = hex(colors[index])[2:]
            time.sleep(0.01)
            continue

        if submit:
            color = ["{:02x}".format(colors[i]) for i in range(len(colors))]
            color = "#" + "".join(color)
            iot.publish("neopixel", color)
            break

        if back:
            break
        time.sleep(0.1)

    display.show(None)
    time.sleep(0.5)
    # display.show(funhouse.splash)
    display.refresh()


display = board.DISPLAY

# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)


def pub_lamp(lamp):
    lamp = eval(lamp)
    iot.publish("lamp", str(not lamp))
    # funhouse.set_text(f"Lamp: {not lamp}", 0)
    time.sleep(0.3)


print(type(board.DISPLAY))
print(type(display))
iot = Hub(display=display, io=io, nav=(up, select, down, back, submit))

iot.add_device(
    feed_key="lamp",
    default_text="Lamp: ",
    formatted_text="Lamp: {}",
    pub_method=pub_lamp,
)
iot.add_device(
    feed_key="temperature",
    default_text="Temperature: ",
    formatted_text="Temperature: {:.1f} C",
)
iot.add_device(
    feed_key="humidity", default_text="Humidity: ", formatted_text="Humidity: {:.2f}%"
)
iot.add_device(
    feed_key="neopixel",
    default_text="LED: ",
    formatted_text="LED: {}",
    color_callback=rgb_set_color,
    pub_method=rgb,
)
iot.add_device(
    feed_key="battery",
    default_text="Battery: ",
    formatted_text="Battery: {}%",
)

iot.get()

while True:
    iot.loop()
    time.sleep(0.01)
