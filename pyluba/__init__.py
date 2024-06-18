# __init__.py

# version of Luba API
# TODO export the three interface types
__version__ = "0.0.5"

import asyncio
import logging
import os

# works outside HA on its own
from pyluba.bluetooth.ble import LubaBLE
from pyluba.http.http import LubaHTTP, connect_http

# TODO make a working device that will work outside HA too.
from pyluba.mammotion.devices import MammotionBaseBLEDevice
from pyluba.mqtt.mqtt import LubaMQTT, logger

# TODO provide interface to pick between mqtt/cloud/bluetooth

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.getChild("paho").setLevel(logging.WARNING)
    PRODUCT_KEY = os.environ.get("PRODUCT_KEY")
    DEVICE_NAME = os.environ.get("DEVICE_NAME")
    DEVICE_SECRET = os.environ.get("DEVICE_SECRET")
    luba = LubaMQTT(region_id="ap-southeast-1", product_key=PRODUCT_KEY, device_name=DEVICE_NAME, device_secret=DEVICE_SECRET, client_id="AOJWO39j")
    luba.connect()


    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()
