from django.core.management.base import BaseCommand, CommandError

from datetime import datetime
import json
import time
import uuid

import redis

"""
Async tasks implementing AsyncCore need to define:

# Class Attributes

 - lead - The log lead string
 - help - Help dumped to command line if there's an error starting this async task
 - control_channel - Of the form: task_async_control_ , this is the channel used to store run time config

# Methods

 - update_settings(options) - pull in new options that may have changed in our channel settings
 - default_settings() -> dict - The dictionary of default settings for the channel
 - handle() - Do your work and keep running while self.keep_running() is True
"""

class AsyncCore(BaseCommand):
    help = 'Default help'
    lead = "[async_core]"

    # redis config
    control_channel = "shipyard_async_control_" + str(uuid.uuid4())

    # run time control - we spin up every 20 seconds
    duty_cycle = 20

    # settings sync - check every 60 seconds for settings updates
    last_settings_sync = 0
    setting_sync_delay = 60

    def __init__(self, *args, **kwargs):
        super(AsyncCore, self).__init__(*args, **kwargs)

        # fix up our control channel
        self.control_channel += str(uuid.uuid4())

        # spin us up
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

        # check for our own things to update
        self.duty_cycle = chan["duty_cycle"]

        self.update_settings(chan)


    def update_settings(self, settings):
        """
        Use your new settings.

        :param settings:
        :return:
        """
        pass

    def default_settings(self):
        """
        Return our default settings as a dict.

        :return:
        """
        return {}

    def seed_control_channel(self):
        """
        What does our basic control channel look like?

        :return:
        """
        control = self.default_settings()

        # feed in some other defaults if they aren't defined
        defaults = {
            "active": True,
            "last_sync": str(datetime.now()),
            "type": self.control_channel.strip("_"),
            "duty_cycle": 20
        }

        for def_k, def_v in defaults.items():
            if def_k not in control:
                control[def_k] = def_v

        # stash it
        self.redis.psetex(self.control_channel, self.duty_cycle * 1000 * 2, json.dumps(control))

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
        self.log("Starting /async_core/")


        self.log("Stopping /async_core/")

    def keep_running(self):
        """
        Check our control channel for settings.

        :return:
        """
        # do our settings house keeping
        now = time.time()
        if now - self.last_settings_sync > self.setting_sync_delay:
            self.log("synchronizing settings")
            self.sync_settings()
            self.last_settings_sync = now

        # grab our control channel
        chan_raw = self.redis.get(self.control_channel)
        chan = json.loads(chan_raw)

        # poke our time
        chan["last_sync"] = str(datetime.now())

        # get our run
        run = chan["active"]

        # store our settings
        self.redis.psetex(self.control_channel, self.duty_cycle * 1000 * 2, json.dumps(chan))

        return run


