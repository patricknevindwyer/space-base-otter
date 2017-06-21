from async_core import AsyncCore

from datetime import datetime
import json
import time
import uuid

import redis

from ui.models import ShipYard


class Command(AsyncCore):
    help = 'Handle asynchronous ShipYard tasks'
    lead = "[shipyard_async]"

    # redis config
    control_channel = "shipyard_async_control_"

    def default_settings(self):
        """
        What does our basic control channel look like?

        :return:
        """
        return {
            "type": "shipyard_async_control"
        }

    def handle(self, *args, **options):
        """
        Handle the async task mode.

        :param args:
        :param options:
        :return:
        """
        self.log("Starting /shipyard_async/")

        while self.keep_running():

            # Let's restock ships
            self.log("starting shipyard resource check")
            yard = ShipYard.objects.too_few_ships_available().first()

            if yard is not None:
                self.log("Restocking shipyard <%s>" % (yard.name,))
                new_ship_count = yard.restock_ships()
                self.log("+ %d ships restocked at <%s>", new_ship_count, yard.name)
            else:
                self.log("% no shipyards needed to be restocked")

            # sleep for a bit
            time.sleep(self.duty_cycle)

        self.log("Stopping /shipyard_async/")