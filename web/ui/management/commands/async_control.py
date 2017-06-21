from django.core.management.base import BaseCommand, CommandError

from datetime import datetime
import json

import redis

"""
Control all of the async services.
"""

class Command(BaseCommand):
    help = 'Inspect and manage async services'
    lead = "[async_control]"

    # control channel prefix mappings, channel prefix pattern -> channel type
    control_prefixes = {
        "shipyard_async_control": "shipyard_async_control_"
    }


    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        # self.log("Connecting to redis")
        self.redis = redis.StrictRedis(host='redis', port=6379, db=0)

    def add_arguments(self, parser):
        parser.add_argument("command", nargs=1)
        parser.add_argument("terms", nargs="*")

        parser.add_argument("--seconds", dest="seconds", type=int, default=20, help="Seconds")

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
        We'll dispatch our command from here.

        :param args:
        :param options:
        :return:
        """

        dispatch_map = {
            "list": self._handle_list,
            "stop": self._handle_stop,
            "expire": self._handle_expire
        }

        dispatch_to = options["command"][0]
        if dispatch_to in dispatch_map:
            dispatch_map[dispatch_to](*args, **options)
        else:
            self.log("The command [%s] was not recognized", dispatch_to)

    def _handle_stop(self, *args, **options):
        """
        stop services by setting the active flag to false. We'll get a list
        of one or more services to kill.

        :param args:
        :param options:
        :return:
        """
        channels = options["terms"]

        if len(channels) == 0:
            self.log("No channels specified to stop")

        for channel in channels:
            channel_key = self.control_prefixes[channel]
            redis_keys = self.redis.keys(channel_key + "*")
            print "Stopping channel(%s) == %d instances" % (channel_key, len(redis_keys))
            for redis_key in redis_keys:
                chan_data = json.loads(self.redis.get(redis_key))
                chan_data["active"] = False
                self.redis.set(redis_key, json.dumps(chan_data))
                print "    - %s deactivated" % (redis_key,)

    def _handle_expire(self, *args, **options):
        """
        Clear our redis of a key prefix. This is not surgical, this is a shotgun. If a channel
        doesn't subsequently update itself, it's config will disappear

        :param args:
        :param options:
        :return:
        """
        channels = options["terms"]
        expire_in = options["seconds"]

        if len(channels) == 0:
            self.log("No channels specified to expire")

        for channel in channels:
            channel_key = self.control_prefixes[channel]
            redis_keys = self.redis.keys(channel_key + "*")
            print "Expiring channel(%s) == %d instances" % (channel_key, len(redis_keys))
            for redis_key in redis_keys:
                self.redis.expire(redis_key, expire_in)
                print "    - %s expiring in %d seconds" % (redis_key, expire_in)


    def _handle_list(self, *args, **options):
        """
        List out the active services.

        :param args:
        :param options:
        :return:
        """
        now = datetime.now()

        for chan_type, prefix in self.control_prefixes.items():
            chans = self.redis.keys(prefix + "*")

            print "channel(%s) == %d instances" % (chan_type, len(chans))

            for chan in chans:

                chan_data = json.loads(self.redis.get(chan))

                # figure out the last sync
                # looks like 2017-06-21 01:29:55.443200
                last_sync = datetime.strptime(chan_data["last_sync"], "%Y-%m-%d %H:%M:%S.%f")
                sync_diff = now - last_sync
                print "    - %s (last sync: %s)" % (chan, str(sync_diff))