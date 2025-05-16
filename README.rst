Introduction
============


.. image:: https://readthedocs.org/projects/adafruit-circuitpython-dash_display/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/dash_display/en/latest/
    :alt: Documentation Status


.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord


.. image:: https://github.com/adafruit/Adafruit_CircuitPython_Dash_Display/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_Dash_Display/actions
    :alt: Build Status


.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

CircuitPython library for creating Adafruit IO dashboards.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_
or individual libraries can be installed using
`circup <https://github.com/adafruit/circup>`_.


Usage Example
=============

.. code :: python3

    import time
    import board
    from digitalio import DigitalInOut, Direction, Pull
    import touchio
    import wifi
    import adafruit_connection_manager
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

    # Get WiFi details and Adafruit IO keys, ensure these are setup in settings.toml
    # (visit io.adafruit.com if you need to create an account, or if you need your Adafruit IO key.)
    ssid = getenv("CIRCUITPY_WIFI_SSID")
    password = getenv("CIRCUITPY_WIFI_PASSWORD")
    aio_username = getenv("ADAFRUIT_AIO_USERNAME")
    aio_key = getenv("ADAFRUIT_AIO_KEY")

    display = board.DISPLAY

    print(f"Connecting to {ssid}")
    wifi.radio.connect(ssid, password)
    print(f"Connected to {ssid}!")

    # Create a socket pool
    pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)

    # Initialize a new MQTT Client object
    mqtt_client = MQTT.MQTT(
        broker="io.adafruit.com",
        username=aio_username,
        password=aio_key,
        socket_pool=pool,
        ssl_context=ssl_context,
    )

    # Initialize an Adafruit IO MQTT Client
    io = IO_MQTT(mqtt_client)


    def pub_lamp(lamp):
        if type(lamp) == str:
            lamp = eval(lamp)
        iot.publish("lamp", str(not lamp))
        # funhouse.set_text(f"Lamp: {not lamp}", 0)
        time.sleep(0.3)


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

    iot.get()

    while True:
        iot.loop()
        time.sleep(0.01)

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/dash_display/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_Dash_Display/blob/HEAD/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
