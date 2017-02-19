from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.dispatch import receiver

import random
import string
import json
import os
import math

# Resource settings we use

# LOAD THE GOODS!
GOODS = json.loads(open("ui/resources/goods.json", "r").read())

# What are our planet images?
planet_range = range(1,8) + range(10, 21)
PLANET_IMAGES = ["planet%d.png" % i for i in planet_range]

# Shipyards
SHIPYARDS = [line.strip() for line in open("ui/resources/shipyards.txt", "r").readlines()]

# Ship types
SHIP_TYPES = [line.strip() for line in open("ui/resources/shiptypes.txt", "r").readlines()]

# SHIP Images
SHIP_IMAGES = [ship for ship in os.listdir("ui/static/ui/images/ships") if ship.endswith("png")]

# Fuel base cost
FUEL_UNIT_COST = 10

###
# User Profile
###
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # by default our users will start with 100,000 credits
    credits = models.IntegerField(default=100000)

    # tallies of user assets
    def assets_ships(self):
        """
        Just do a quick tally of ship values.

        :return:
        """
        v = 0
        for ship in self.ships.all():
            v += ship.value

        return v

    def add_credits(self, creds):
        self.credits += creds
        self.save()

    def subtract_credits(self, creds, go_negative=False):
        self.credits -= creds

        if self.credits < 0 and not go_negative:
            self.credits = 0

        self.save()

@receiver(user_logged_in)
def user_post_login(sender, user, request, **kwargs):
    """
    Do anything we need post login.

    :param sender:
    :param user:
    :param request:
    :param kwargs:
    :return:
    """
    print "% models.py::user_post_login"

    # make sure we have a profile for this user
    if not  hasattr(user, "profile"):
        print "%% creating a profile for %s" % (user.username,)
        profile = Profile.objects.create(
            user=user
        )
        profile.save()



###
# PLANETS
###
class PlanetManager(models.Manager):
    """
    Query, build, and otherwise manipulate Planets.
    """

    def pick_random(self):
        """
        Pick a random plane that we already have available.

        :return:
        """
        id = random.sample(self.only("id").all(), 1)
        return id[0]

    def create_random(self):
        """
        Create and place a random Planet.

        :return:
        """

        # coordinates
        x_co = random.randrange(-1000, 1000)
        y_co = random.randrange(-1000, 1000)

        # now we need a name
        planet_name = self.random_planet_name()

        # we also need to pick out an image
        planet_image = random.sample(PLANET_IMAGES,1)[0]

        # make our planet
        obj = self.create(
            name = planet_name,

            x_coordinate = x_co,
            y_coordinate = y_co,

            image_name = planet_image
        )

        # let's add some imports
        num_imports = random.randint(3, 6)
        ims = random.sample(GOODS, num_imports)
        for im in ims:
            candidate = random.random()
            if candidate >= im["liklihood"]["import"]:
                p_import = Good.objects.create(
                    planet = obj,
                    name = im["good"],
                    is_import = True,
                    is_export = False,
                    price = random.uniform(im["price"]["import"]["min"], im["price"]["import"]["max"]) * im["price"]["base"]
                )

        # let's add some exports
        num_imports = random.randint(3, 6)
        ims = random.sample(GOODS, num_imports)
        for im in ims:
            candidate = random.random()
            if candidate >= im["liklihood"]["export"]:
                p_import = Good.objects.create(
                    planet = obj,
                    name = im["good"],
                    is_import = False,
                    is_export = True,
                    price = random.uniform(im["price"]["export"]["min"], im["price"]["export"]["max"]) * im["price"]["base"]
                )


        return obj

    def random_planet_name(self):
        """
        Generate a random planet name.

        :return:
        """

        # get a good prefix
        planet_prefix = ""
        with open("ui/resources/planet_prefix.list", "r") as prefixes:
            planet_prefix = random.sample([prefix.strip() for prefix in prefixes.readlines()], 1)[0]

        # pick a designator
        planet_number = random.randint(1000, 10000)

        # system location?
        planet_orbit = random.sample(string.ascii_uppercase, 1)[0]

        return "%s %d-%s" % (planet_prefix, planet_number, planet_orbit)

class Planet(models.Model):
    """
    Describe a planet.
    """
    objects = PlanetManager()

    name = models.CharField(max_length=255, null=False, blank=False)

    # where is this planet?
    x_coordinate = models.IntegerField(default=0, null=False, blank=False)
    y_coordinate = models.IntegerField(default=0, null=False, blank=False)

    # some display settings
    image_name = models.CharField(max_length=255, null=False, blank=False)

    # rarity of fuel effects the overall refueling cost. This is some sane number
    # basically [50% - 200%] of standard price
    fuel_markup = models.FloatField(default=1.0)

    def imports(self):
        return self.goods.filter(is_import=True)

    def exports(self):
        return self.goods.filter(is_export=True)


###
# GOODS
###
class Good(models.Model):
    """
    An instance of a good or service, linked to a Planet or a Ship.
    """

    name = models.CharField(max_length=255, null=False, blank=False)

    # what planet has these goods?
    planet = models.ForeignKey(Planet, on_delete=models.CASCADE, related_name="goods")

    # is this an import
    is_import = models.BooleanField(null=False)

    # is this an export
    is_export = models.BooleanField(null=False)

    # Prices
    price = models.FloatField(null=False, blank=False)

###
# SHIPS
###
def get_default_ship_location():
    return Planet.objects.first()

class ShipManager(models.Manager):
    """
    Work with ships.
    """

    def create_random(self):
        """
        Generate a random ship.

        :return:
        """

        # pick our yard and type
        shipyard = random.sample(SHIPYARDS, 1)[0]
        shiptype = random.sample(SHIP_TYPES, 1)[0]

        # what do we name this ship
        ship_name = shiptype

        # what's the model of this ship
        ship_model = "%s %s" % (shipyard, shiptype)

        # starting planet
        ship_planet = Planet.objects.first()
        ship_home_planet = Planet.objects.pick_random()

        ship_range = random.randint(200, 500)
        ship_fuel_level = 100.0
        ship_cargo_cap = random.randint(50, 500)

        # ship value?
        ship_markup = random.uniform(0.2, 1.5)
        ship_value = int(ship_range * ship_cargo_cap * ship_markup)

        # what about an image for this ship?
        ship_image = random.sample(SHIP_IMAGES, 1)[0]

        obj = self.create(
            name = ship_name,
            model = ship_model,
            planet = ship_planet,
            home_planet = ship_home_planet,
            max_range = ship_range,
            fuel_level = ship_fuel_level,
            cargo_capacity = ship_cargo_cap,
            image_name = ship_image,
            value=ship_value
        )

        return obj


class Ship(models.Model):
    """
    A base model class for ships
    """
    objects = ShipManager()

    name = models.CharField(max_length=255, null=False, blank=False)

    # who owns this ship?
    owner = models.ForeignKey(Profile, null=True, blank=True, related_name="ships")

    # how much does this ship worth?
    value = models.IntegerField(default=10000)

    # what type of ship was this?
    model = models.CharField(max_length=255, null=False, blank=False)

    # a ship is at a planet
    planet = models.ForeignKey(Planet, null=False, blank=False, on_delete=models.SET(get_default_ship_location), related_name="orbiters")

    # a ship also has a home planet
    home_planet = models.ForeignKey(Planet, null=False, blank=False, on_delete=models.SET(get_default_ship_location), related_name="registrants")

    # some basic settings that we'll improve upon later

    # how far can we go on a full tank?
    max_range = models.IntegerField(null=False, blank=False, default=1000)

    # for now we'll treat fuel as a perentage of a tank of fuel
    fuel_level = models.FloatField(null=False, blank=False, default=100.0)

    # how much cargo space do we have?
    cargo_capacity = models.IntegerField(null=False, blank=False, default=50)

    # image for this ship?
    image_name = models.CharField(max_length=255, null=False, blank=False)

    def current_range(self):
        """
        How far could this ship go right now?

        :return:
        """
        print "max range(%f) * fuel level(%f) / 100.0" % (self.max_range, self.fuel_level)
        return self.max_range * (self.fuel_level / 100.0)

    def current_cargo_load(self):
        """
        What's the capacity impact of our current cargo?
        :return:
        """
        return 0

    def cargo_load_percent(self):
        """
        What percent of our cargo hold is filled?

        :return:
        """
        return self.current_cargo_load() / self.cargo_capacity * 100.0

    def planets_in_range(self):
        """
        Find the planets that are in range, and compute a bit of data
        :return:
        """
        plist = []

        # figure out how far we can go
        max_range = self.current_range()

        # bail out if we're reaaaaaally low on fuel
        if max_range < 1:
            return plist

        # preselect a set of planets in the box that our max range describes
        min_x = self.planet.x_coordinate - max_range
        max_x = self.planet.x_coordinate + max_range
        min_y = self.planet.y_coordinate - max_range
        max_y = self.planet.y_coordinate + max_range

        close_enough = Planet.objects.filter(
            x_coordinate__gte=min_x,
            x_coordinate__lte=max_x,
            y_coordinate__gte=min_y,
            y_coordinate__lte=max_y
        ).all()

        for planet in close_enough:

            # now do a real distance calculation
            real_dist = self.distance_to(planet)
            if real_dist > self.current_range():
                continue

            # ok! our planet is close enough
            plist.append(
                {
                    "name": planet.name,
                    "id": planet.id,
                    "distance": real_dist,
                    "fuel_burned_percent": real_dist / max_range * 100.0
                }
            )
        plist.sort(key=lambda s: s["distance"])

        return plist

    def distance_to(self, planet):
        """
        How far is it to the given planet.

        :param planet:
        :return:
        """
        return math.sqrt(((self.planet.x_coordinate - planet.x_coordinate)**2) + ((self.planet.y_coordinate - planet.y_coordinate)**2))

    def travel_to(self, planet):
        """
        Update the ship for travel to a planet.

        :param planet:
        :return:
        """
        self.planet = planet
        self.save()

    def is_home_planet_in_range(self):
        """
        Is our home planet within travel distance?

        :return:
        """
        return self.current_range() > self.distance_to(self.home_planet)

    def is_home(self):
        return self.planet == self.home_planet

    def burn_fuel_for_distance(self, dist):
        """
        Burn enough fuel to travel a particular distance.

        :param dist:
        :return:
        """
        perc_burn = dist * 1.0 / self.max_range * 100.0
        self.fuel_level = self.fuel_level - perc_burn
        self.save()

    def fuel_units(self):
        """
        what's our current break down of available/used fuel units?
        :return:
        """
        available = self.fuel_level / 100 * self.max_range
        used = self.max_range - available
        return (used, available)

    def can_fully_refuel(self):
        """
        Can we afford to fully refuel this ship?

        :return:
        """
        return self.owner.credits > self.refuel_cost()

    def refuel_cost(self):
        """
        What's the cost to refuel on our current planet? We need to take
        into account the possibility of not having enough money to fully
        refuel.

        :return:
        """

        # how many units of fuel do we need
        f_used, f_available = self.fuel_units()

        # given the planet markup, what will our used fuel cost to
        # replace?
        cost = FUEL_UNIT_COST * self.planet.fuel_markup * f_used
        return cost

    def refuel(self):
        """
        Fully refuel.

        :return:
        """
        self.fuel_level = 100.0
        self.save()

    def partially_refuel(self, creds):
        """
        Apply X creds towards refueling.

        :param creds:
        :return:
        """
        # figure out what % of our fuel level we can recoup for X credits
        cost = self.refuel_cost()
        f_used, f_available = self.fuel_units()

        refuel_units = creds * 1.0 / cost * f_used
        refuel_perc = refuel_units / self.max_range * 100.0
        self.fuel_level += refuel_perc
        self.save()
