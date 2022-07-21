# SPDX-FileCopyrightText: Copyright (c) 2021 Eva Herrada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_dash_display`
================================================================================
CircuitPython library for creating Adafruit IO dashboards.

* Author(s): Eva Herrada

Implementation Notes
--------------------
**Hardware:**

* This library currently only officially supports the
  `Adafruit Funhouse <https://www.adafruit.com/product/4985>`_ but other boards are coming soon.

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import time
from collections import OrderedDict
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label
import displayio
import terminalio

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Dash_Display.git"


class Feed:
    """Feed object to make getting and setting different feed properties easier"""

    def __init__(
        self, key, default_text, formatted_text, callback, color, pub, index
    ):  # pylint: disable=too-many-arguments
        self._key = key
        self.default_text = default_text
        self._text = formatted_text
        self._callback = callback
        self._color = color
        self._pub = pub
        self.index = index

        self._last_val = None

    @property
    def key(self):
        """Getter for feed key. Will give the value of the feed key"""
        return self._key

    @key.setter
    def key(self, value):
        """Setter for feed key. Sets a new value for the feed key property _key"""
        self._key = value

    @property
    def text(self):
        """Getter for text ready to be formatted. Will give the feed text"""
        return self._text

    @text.setter
    def text(self, value):
        """Setter for text ready to be formatted. Allows to change the feed text"""
        self._text = value

    @property
    def callback(self):
        """Getter for callback function. Returns the feed callback"""
        return self._callback

    @callback.setter
    def callback(self, value):
        """Setter for callback function. Changes the feed callback"""
        self._callback = value

    @property
    def color(self):
        """Getter for text color callback function. Will return the color for the feed"""
        return self._color

    @color.setter
    def color(self, value):
        """Setter for text color callback function"""
        self._color = value

    @property
    def pub(self):
        """Getter for publish function, called when a new value is published by this library."""
        return self._pub

    @pub.setter
    def pub(self, value):
        """Setter for publish function"""
        self._pub = value

    @property
    def last_val(self):
        """Getter for the last value received"""
        return self._last_val

    @last_val.setter
    def last_val(self, value):
        """Setter for last received value"""
        self._last_val = value


class Hub:  # pylint: disable=too-many-instance-attributes
    """Object that lets you make an IOT dashboard"""

    def __init__(self, display, io, nav):
        self.display = display

        self.io = io  # pylint: disable=invalid-name

        self.up_btn, self.select, self.down, self.back, self.submit = nav

        self.length = 0
        self.selected = 1

        self.feeds = OrderedDict()

        self.io.on_mqtt_connect = self.connected
        self.io.on_mqtt_disconnect = self.disconnected
        self.io.on_mqtt_subscribe = self.subscribe
        self.io.on_message = self.message

        print("Connecting to Adafruit IO...")
        io.connect()

        self.display.show(None)

        self.splash = displayio.Group()

        self.rect = Rect(0, 0, 240, 30, fill=0xFFFFFF)
        self.splash.append(self.rect)

        self.display.show(self.splash)

    def simple_text_callback(
        self, client, feed_id, message
    ):  # pylint: disable=unused-argument
        """Default callback function that uses the text in the Feed object and the color callback
        to set the text"""
        feed_id = feed_id.split("/")[-1]
        feed = self.feeds[feed_id]
        try:
            text = feed.text.format(message)
        except ValueError:
            text = feed.text.format(float(message))
        return text

    def update_text(self, client, feed_id, message):
        """Updates the text on the display"""
        feed = self.feeds[feed_id]
        feed.callback(client, feed_id, message)
        self.splash[feed.index + 1].text = feed.callback(client, feed_id, str(message))
        if feed.color:
            self.splash[feed.index + 1].color = feed.color(message)

    def base_pub(self, var):
        """Default function called when a feed is published to"""

    def add_device(
        self,
        feed_key,
        default_text=None,
        formatted_text=None,
        color_callback=None,
        callback=None,
        pub_method=None,
    ):  # pylint: disable=too-many-arguments
        """Adds a feed/device to the UI"""
        if not callback:
            callback = self.simple_text_callback
        if not pub_method:
            pub_method = self.base_pub
        if not formatted_text:
            formatted_text = f"{feed_key} : "
            formatted_text = formatted_text + "{}"
        if not default_text:
            default_text = feed_key

        self.io.subscribe(feed_key)
        if len(self.splash) == 1:
            self.splash.append(
                Label(
                    font=terminalio.FONT,
                    text=default_text,
                    x=3,
                    y=15,
                    anchored_position=(3, 15),
                    scale=2,
                    color=0x000000,
                )
            )
        else:
            self.splash.append(
                Label(
                    font=terminalio.FONT,
                    x=3,
                    y=((len(self.splash) - 1) * 30) + 15,
                    text=default_text,
                    color=0xFFFFFF,
                    anchored_position=(3, ((len(self.splash) - 2) * 30) + 15),
                    scale=2,
                )
            )
        self.length = len(self.splash) - 2
        self.feeds[feed_key] = Feed(
            key=feed_key,
            default_text=default_text,
            formatted_text=formatted_text,
            callback=callback,
            color=color_callback,
            pub=pub_method,
            index=len(self.feeds),
        )

    def get(self):
        """Gets all the subscribed feeds"""
        for feed in self.feeds.keys():
            print(f"getting {feed}")
            self.io.get(feed)
            time.sleep(0.1)
        self.io.loop()

    # pylint: disable=unused-argument
    @staticmethod
    def connected(client):
        """Callback for when the device is connected to Adafruit IO"""
        print("Connected to Adafruit IO!")

    @staticmethod
    def subscribe(client, userdata, topic, granted_qos):
        """Callback for when a new feed is subscribed to"""
        print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))

    @staticmethod
    def disconnected(client):
        """Callback for when the device disconnects from Adafruit IO"""
        print("Disconnected from Adafruit IO!")

    def message(self, client, feed_id, message):
        """Callback for whenever a new message is received"""
        print("Feed {0} received new value: {1}".format(feed_id, message))
        feed_id = feed_id.split("/")[-1]
        feed = self.feeds[feed_id]
        feed.last_val = message
        self.update_text(client, feed_id, str(message))

    def publish(self, feed, message):
        """Callback for publishing a message"""
        print(f"Publishing {message} to {feed}")
        self.io.publish(feed, message)

    def loop(self):
        """Loops Adafruit IO and also checks to see if any buttons have been pressed"""
        self.io.loop()
        if self.select.value:
            feed = self.feeds[list(self.feeds.keys())[self.selected - 1]]
            if feed.pub:
                feed.pub(feed.last_val)
                self.display.show(self.splash)
            while self.select.value:
                pass

        if self.down.value and self.selected < self.length + 1:
            rgb = self.splash[self.selected].color
            color = (
                ((255 - ((rgb >> 16) & 0xFF)) << 16)
                + ((255 - ((rgb >> 8) & 0xFF)) << 8)
                + (255 - (rgb & 0xFF))
            )
            self.splash[self.selected].color = color

            self.rect.y += 30
            self.selected += 1

            rgb = self.splash[self.selected].color
            color = (
                ((255 - ((rgb >> 16) & 0xFF)) << 16)
                + ((255 - ((rgb >> 8) & 0xFF)) << 8)
                + (255 - (rgb & 0xFF))
            )
            self.splash[self.selected].color = color

        if self.up_btn.value and self.selected > 1:
            rgb = self.splash[self.selected].color
            color = (
                ((255 - ((rgb >> 16) & 0xFF)) << 16)
                + ((255 - ((rgb >> 8) & 0xFF)) << 8)
                + (255 - (rgb & 0xFF))
            )
            self.splash[self.selected].color = color

            self.rect.y -= 30
            self.selected -= 1

            rgb = self.splash[self.selected].color
            color = (
                ((255 - ((rgb >> 16) & 0xFF)) << 16)
                + ((255 - ((rgb >> 8) & 0xFF)) << 8)
                + (255 - (rgb & 0xFF))
            )
            self.splash[self.selected].color = color
