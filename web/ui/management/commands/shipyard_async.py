from django.core.management.base import BaseCommand, CommandError

from datetime import datetime
import json
import time
import uuid

import redis

from ui.models import ShipYard


class Command(BaseCommand):
    help = 'Handle asynchronous ShipYard tasks'
    lead = "[shipyard_async]"

    # redis config
    control_channel = "shipyard_async_control_" + str(uuid.uuid4())

    # run time control - we spin up every 20 seconds
    duty_cycle = 20

    # settings sync - check every 60 seconds for settings updates
    last_settings_sync = 0
    setting_sync_delay = 60

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.log("Connecting to redis")
        self.redis = redis.StrictRedis(host='redis', port=6379, db=0)
        self.seed_control_channel()

    def sync_settings(self):
        """
        Pull in our settings from Redis, and sync anything
        we need to.

        :return:
        """
        chan_raw = self.redis.get(self.control_channel)
        chan = json.loads(chan_raw)
        self.duty_cycle = chan["duty_cycle"]

    def seed_control_channel(self):
        """
        What does our basic control channel look like?

        :return:
        """
        control = {
            "active": True,
            "last_sync": str(datetime.now()),
            "duty_cycle": 20,
            "type": "shipyard_async_control"
        }

        self.redis.set(self.control_channel, json.dumps(control))

    def log(self, msg, *kargs, **kwargs):
        """
        Simple logging output.

        :param msg:
        :return:
        """
        if len(kargs) > 0:
            msg = msg % kargs
        if len(kwargs) > 0:
            msg = msg % kwargs

        print "%s [%s] - %s" % (self.lead, str(datetime.now()), msg)

    def handle(self, *args, **options):
        """
        Handle the async task mode.

        :param args:
        :param options:
        :return:
        """
        self.log("Starting /shipyard_async/")

        while self.keep_running():

            # do our settings house keeping
            now = time.time()
            if now - self.last_settings_sync > self.setting_sync_delay:
                self.log("synchronizing settings")
                self.sync_settings()
                self.last_settings_sync = now

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

    def keep_running(self):
        """
        Check our control channel for settings.

        :return:
        """

        # grab our control channel
        chan_raw = self.redis.get(self.control_channel)
        chan = json.loads(chan_raw)

        # poke our time
        chan["last_sync"] = str(datetime.now())

        # get our run
        run = chan["active"]

        # store our settings
        self.redis.set(self.control_channel, json.dumps(chan))

        return run


