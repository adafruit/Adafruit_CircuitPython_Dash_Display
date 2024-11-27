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
try:
    from typing import Tuple, Callable, Optional, Any
    from adafruit_io.adafruit_io import IO_MQTT
    from digitalio import DigitalInOut
except ImportError:
    pass

import time
from collections import OrderedDict
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text.label import Label

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Dash_Display.git"


class Feed:
    """Feed object to make getting and setting different feed properties easier

    :param str key: The Adafruit IO key.
    :param str default_text: Text to display before data has been pulled from Adafruit IO.
    :param str formatted_text: String with formatting placeholders within it ready to have
        data formatted into it.
    :param Callable callback: A function to call when the feed is fetched.
    :param int color: Hex color code for the feed text.
    :param Callable pub: a function to call when data is published to the feed.

    """

    def __init__(
        self,
        key: str,
        default_text: str,
        formatted_text: str,
        callback: Optional[Callable],
        color: Optional[int],
        pub: Optional[Callable],
        index: int,
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
    def key(self) -> str:
        """Getter for feed key. Will give the value of the feed key"""
        return self._key

    @key.setter
    def key(self, value: str) -> None:
        """Setter for feed key. Sets a new value for the feed key property _key

        :param str value: The new value of the feed key.
        """
        self._key = value

    @property
    def text(self) -> str:
        """Getter for text ready to be formatted. Will give the feed text"""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Setter for text ready to be formatted. Allows to change the feed text

        :param str value: The new value of the feed text.
        """
        self._text = value

    @property
    def callback(self) -> Optional[Callable]:
        """Getter for callback function. Returns the feed callback"""
        return self._callback

    @callback.setter
    def callback(self, value: Callable) -> None:
        """Setter for callback function. Changes the feed callback

        :param Callable value: A function to call when the feed is fetched.
        """
        self._callback = value

    @property
    def color(self) -> int:
        """Getter for text color callback function. Will return the color for the feed"""
        return self._color

    @color.setter
    def color(self, value: int) -> None:
        """Setter for text color callback function

        :param int value: The new value of the feed color.
        """
        self._color = value

    @property
    def pub(self) -> Optional[Callable]:
        """Getter for publish function, called when a new value is published by this library."""
        return self._pub

    @pub.setter
    def pub(self, value: Callable) -> None:
        """Setter for publish function"""
        self._pub = value

    @property
    def last_val(self) -> Optional[str]:
        """Getter for the last value received"""
        return self._last_val

    @last_val.setter
    def last_val(self, value: str) -> None:
        """Setter for last received value

        :param str value: The newly received value.
        """
        self._last_val = value


class Hub:  # pylint: disable=too-many-instance-attributes
    """
    Object that lets you make an IOT dashboard

    :param displayio.Display display: The display for the dashboard.
    :param IO_MQTT io_mqtt: MQTT communications object.
    :param Tuple[DigitalInOut, ...] nav: The navigation pushbuttons.
    """

    def __init__(
        self,
        display: displayio.Display,
        io_mqtt: IO_MQTT,
        nav: Tuple[DigitalInOut, ...],
    ):
        self.display = display

        self.io_mqtt = io_mqtt

        self.up_btn, self.select, self.down, self.back, self.submit = nav

        self.length = 0
        self.selected = 1

        self.feeds = OrderedDict()

        self.io_mqtt.on_mqtt_connect = self.connected
        self.io_mqtt.on_mqtt_disconnect = self.disconnected
        self.io_mqtt.on_mqtt_subscribe = self.subscribe
        self.io_mqtt.on_message = self.message

        print("Connecting to Adafruit IO...")
        io_mqtt.connect()

        self.display.root_group = None

        self.splash = displayio.Group()

        self.rect = Rect(0, 0, 240, 30, fill=0xFFFFFF)
        self.splash.append(self.rect)

        self.display.root_group = self.splash

    def simple_text_callback(
        # pylint: disable=unused-argument
        self,
        client: IO_MQTT,
        feed_id: str,
        message: str,
    ) -> str:
        """Default callback function that uses the text in the Feed object and the color callback
        to set the text

        :param IO_MQTT client: The MQTT client to use.
        :param str feed_id: The Adafruit IO feed ID.
        :param str message: The text to display.
        :return: A string with data formatted into it.
        """
        feed_id = feed_id.split("/")[-1]
        feed = self.feeds[feed_id]
        try:
            text = feed.text.format(message)
        except ValueError:
            text = feed.text.format(float(message))
        return text

    def update_text(self, client: IO_MQTT, feed_id: str, message: str) -> None:
        """Updates the text on the display

        :param IO_MQTT client: The MQTT client to use.
        :param str feed_id: The Adafruit IO feed ID.
        :param str message: The text to display.
        """
        feed = self.feeds[feed_id]
        feed.callback(client, feed_id, message)
        self.splash[feed.index + 1].text = feed.callback(client, feed_id, str(message))
        if feed.color:
            self.splash[feed.index + 1].color = feed.color(message)

    def base_pub(self, var: Any) -> None:
        """Default function called when a feed is published to"""

    def add_device(
        self,
        feed_key: str,
        default_text: Optional[str] = None,
        formatted_text: Optional[str] = None,
        color_callback: Optional[int] = None,
        callback: Optional[Callable] = None,
        pub_method: Optional[Callable] = None,
    ):  # pylint: disable=too-many-arguments
        """Adds a feed/device to the UI

        :param feed_key: The Adafruit IO feed key.
        :param str default_text: The default text for the device.
        :param str formatted_text: The formatted text for the device.
        :param int color_callback: The color to use for the device
        :param Callable callback: The callback function to be called
            when data is fetched.
        :param Callable pub_method: The pub_method to be called
            when data is published.
        """
        if not callback:
            callback = self.simple_text_callback
        if not pub_method:
            pub_method = self.base_pub
        if not formatted_text:
            formatted_text = f"{feed_key} : "
            formatted_text = formatted_text + "{}"
        if not default_text:
            default_text = feed_key

        self.io_mqtt.subscribe(feed_key)
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

    def get(self) -> None:
        """Gets all the subscribed feeds"""
        for feed in self.feeds.keys():
            print(f"getting {feed}")
            self.io_mqtt.get(feed)
            time.sleep(0.1)
        self.io_mqtt.loop()

    # pylint: disable=unused-argument
    @staticmethod
    def connected(client: IO_MQTT) -> None:
        """Callback for when the device is connected to Adafruit IO

        :param IO_MQTT client: The MQTT client to use.
        """
        print("Connected to Adafruit IO!")

    @staticmethod
    def subscribe(client: IO_MQTT, userdata: Any, topic: str, granted_qos: str) -> None:
        """Callback for when a new feed is subscribed to

        :param IO_MQTT client: The MQTT client to use.
        :param str userdata: The userdata to subscribe to.
        :param str topic: The topic to subscribe to.
        :param str granted_qos: The QoS level.
        """
        print(f"Subscribed to {topic} with QOS level {granted_qos}")

    @staticmethod
    def disconnected(client: IO_MQTT) -> None:
        """Callback for when the device disconnects from Adafruit IO

        :param IO_MQTT client: The MQTT client to use.
        """
        print("Disconnected from Adafruit IO!")

    def message(self, client: IO_MQTT, feed_id: str, message: str) -> None:
        """Callback for whenever a new message is received

        :param IO_MQTT client: The MQTT client to use.
        :param str feed_id: The Adafruit IO feed ID.
        :param str message: The message received.
        """
        print(f"Feed {feed_id} received new value: {message}")
        feed_id = feed_id.split("/")[-1]
        feed = self.feeds[feed_id]
        feed.last_val = message
        self.update_text(client, feed_id, str(message))

    def publish(self, feed: Feed, message: str) -> None:
        """Callback for publishing a message

        :param Feed feed: The feed to publish to.
        :param str message: The message to publish.
        """
        print(f"Publishing {message} to {feed}")
        self.io_mqtt.publish(feed, message)

    def loop(self) -> None:
        """Loops Adafruit IO and also checks to see if any buttons have been pressed"""
        self.io_mqtt.loop()
        if self.select.value:
            feed = self.feeds[list(self.feeds.keys())[self.selected - 1]]
            if feed.pub:
                feed.pub(feed.last_val)
                self.display.root_group = self.splash
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
