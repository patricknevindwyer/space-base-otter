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
GOODS = json.load(open("ui/resources/goods.json", "r"))

# What are our planet images?
planet_range = range(1,8) + range(10, 21)
PLANET_IMAGES = ["planet%d.png" % i for i in planet_range]

# Shipyards
# TODO: refactor to shipyards.json for creating shipyard
SHIPYARDS = json.load(open("ui/resources/shipyards.json", "r"))

# Ship types
# TODO: refactor to shiptypes.json for the possible variants of ships
SHIP_TYPES = [line.strip() for line in open("ui/resources/shiptypes.txt", "r").readlines()]

# SHIP Images
SHIP_IMAGES = [ship for ship in os.listdir("ui/static/ui/images/ships") if ship.endswith("png")]

# Fuel base cost
FUEL_UNIT_COST = 10

# What are our upgrade qualities?
UPGRADES = json.load(open("ui/resources/upgrades.json", "r"))

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

    def create_random(self, has_shipyard=True):
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

        # do we have a shipyard?
        if has_shipyard:
            yard = ShipYard.objects.create_random_on_planet(obj)

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
# CARGO
###
class Cargo(models.Model):
    """
    A unit of cargo carried by a ship. When new cargo is purchased, this
    object is updated with the total price purchased/sold, so we can keep
    a cost average for the good. When this good quantity hits zero, it
    should be removed from a ship.

    Cargo are compared to good via the **name** field.
    """

    name = models.CharField(max_length=255, null=False, blank=False)

    # how many do we have?
    quantity = models.IntegerField(default=0, null=False)

    # what is the total value of the good?
    total_value = models.FloatField(null=False, blank=False, default=0.0)

    # what ship does this belong to?
    ship = models.ForeignKey("Ship", on_delete=models.CASCADE, related_name="cargo")

    def average_price(self):
        """
        What's the average sale price per unit of cargo?

        :return:
        """
        if self.quantity == 0:
            return 0.0
        else:
            return self.total_value / self.quantity

    def buy(self, good, quantity):
        """
        We're buying more of something! Hooray! Let's do some house keeping.

        :param good:
        :param quantity:
        :return:
        """
        self.quantity += quantity

        # how much have we paid, in total, for all of this?
        self.total_value += (quantity * good.price)

        self.save()

    def sell(self, good, quantity):
        """
        We're selling something off. Update the quantity and average total value.

        :param good:
        :param quantity:
        :return:
        """

        # keep track of our average
        avg_price = self.total_value / self.quantity

        # update cargo
        self.quantity -= quantity

        # update total value with avg price
        self.total_value = self.quantity * avg_price

        self.save()


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
        #shipyard = random.sample(SHIPYARDS, 1)[0]
        shiptype = random.sample(SHIP_TYPES, 1)[0]

        # what do we name this ship
        ship_name = shiptype

        # what's the model of this ship
        #ship_model = "%s %s" % (shipyard, shiptype)
        ship_model = shiptype

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


class ShipUpgradeManager(models.Manager):
    """
    Manage how we generate new ship upgrades, using the UPGRADES data.
    """

    def create_cargo_upgrades(self):
        """
        Create a set of cargo goods, based upon rarity, cost, grade, etc.
            
            0. Given a grade of good, and a component...        
            1. Determine if the component exist at the given grade
            2. Calculate the *size* modification
            3. Calculate the *capacity* requirement
            4. Calculate the *cost*
        
        The result of this method will be 0 or more Cargo components.
        
        :return: 
        """
        upgrades = []

        # let's iterate over our components
        for component in UPGRADES["components"]["cargo"]:

            # let's iterate over our grades
            for grade in UPGRADES["grades"]:

                # is this available?
                candidate = random.random()

                if candidate <= grade["availability"]:

                    # we carry this good!
                    upgrade = self._create_cargo_upgrade(component, grade)
                    upgrades.append(upgrade)

        return upgrades

    def _create_cargo_upgrade(self, component, grade):
        """
        Combine the component and grade to create a new upgrade.
        
        :param component: 
        :param grade: 
        :return: 
        """
        upgrade = self.create(
            size=component["base_size"] * grade["size_modifier"],
            target="cargo",
            ship=None,
            cost=component["base_cost"] * grade["cost_modifier"],
            name=component["name"] + ", " + grade["name"] + " grade",
            quality=grade["name"],
            capacity=component["capacity"],
            description="Cargo: %s, Grade: %s" % (component["description"], grade["description"])
        )
        return upgrade

    def create_cargo_upgrade(self):
        """
        Create a single cargo upgrade to restock or expand the availability at a shipyard. We
        randomly select component type and upgrade until we get a candidate match.
         
        :return: 
        """

        while True:
            component = random.choice(UPGRADES["components"]["cargo"])
            grade = random.choice(UPGRADES["grades"])
            candidate = random.random()

            if candidate <= grade["availability"]:

                # we got one!
                return self._create_cargo_upgrade(component, grade)


class ShipYardManager(models.Manager):

    def create_random_on_planet(self, planet):
        """
        Generate a new ship yard.
        
        We use:
        
         - SHIPYARDS::names - Data for generating ship yard names
        
        :return: 
        """
        yard = self.create(
            name=self._create_name(),
            planet=planet
        )
        yard.save()
        return yard

    def _create_name(self):
        """
        Use the data in SHIPYARDS::names. We have prefixes, suffixes, and
        names. For each of prefixes and suffixes we:
        
         - Walk through the list of prefix/suffix in order, and generate a candidate
           random normal. If that candidate < the prefix/suffix _probability_, then
           we use that prefix/suffix.
           
         - Randomly choose values from the SHIPYARDS::names::names
         
        :return: 
        """

        name_count = random.choice([1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3])


        # prefix
        name_prefix = ""

        for prefix in SHIPYARDS["names"]["prefixes"]:

            # should we use this value?
            candidate = random.random()

            if candidate < prefix["probability"]:
                name_prefix = prefix["prefix"]
                break

        # suffix
        name_suffix = ""

        for suffix in SHIPYARDS["names"]["suffixes"]:

            # should we use this value?
            candidate = random.random()

            if candidate < suffix["probability"]:
                name_suffix = suffix["suffix"]
                break

        # choice of name components
        base_name = random.sample(SHIPYARDS["names"]["names"], name_count)

        return " ".join([name_prefix] + base_name + [name_suffix])


class ShipYard(models.Model):
    """
    Some planets have ship yards. Ship yards hold upgrades and ships for purchase.
    """
    objects = ShipYardManager()

    # descriptive name of the shipyard
    name = models.CharField(max_length=255, blank=False, null=False)

    # what planet does this belong on?
    planet = models.ForeignKey(Planet, related_name="shipyards")

    def name_display(self):
        """
        Turn the name into a better format for display.
        
        :return: 
        """
        return " ".join([word.capitalize() for word in self.name.split(" ")])

    def seed_upgrades(self):
        """
        Setup the upgrades available at a ShipYard.
        
        :return: 
        """
        pass

    def restock_upgrades(self, quantity=1):
        """
        Restock the supply of upgrades.
        
        :return: 
        """
        pass

    def seed_ships(self):
        """
        What ships are available for purchase?
        
        :return: 
        """
        pass

    def restock_ships(self):
        """
        What ships are availale for purchase?
        
        :return: 
        """
        pass

    def purchase_upgrade(self, upgrade):
        """
        Process the given upgrade as purchased.
        
        :param upgrade: 
        :return: 
        """
        pass

    def purchase_ship(self, ship):
        """
        Process the given ship as purchased.
        
        :param ship: 
        :return: 
        """
        pass


class ShipUpgrade(models.Model):
    """
    Upgrades to the ship.
    
    """
    objects = ShipUpgradeManager()

    # how much does this change our ship
    size = models.IntegerField(null=False, blank=False, default=10)

    # what on our ship does this change?
    target = models.CharField(max_length=100, null=False, blank=False, default="cargo")

    # which ship is this upgrade on?
    ship = models.ForeignKey("Ship", blank=True, null=True, related_name="upgrades")

    # what did this upgrade cost
    cost = models.IntegerField(null=False, blank=False, default=100000)

    # what do we call this?
    name = models.CharField(max_length=255, null=False, blank=False)

    # what quality is this upgrade?
    quality = models.CharField(max_length=10, null=False, blank=False)

    # how much cargo capacity does this take up?
    capacity = models.IntegerField(null=False, blank=False, default=10)

    # do we have a description?
    description = models.TextField(null=True, blank=True)


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

    # how much of our upgrade space has already been consumed?
    upgrade_capacity = models.IntegerField(null=False, blank=False, default=0)

    # what's our maximum upgrade capacity? we can expand this with ShipUpgrades. this capacity
    # can be used for multiple things: expanded cargo, expanded range
    upgrade_capactiy_max = models.IntegerField(null=False, blank=False, default=50)

    # image for this ship?
    image_name = models.CharField(max_length=255, null=False, blank=False)

    def install_upgrade(self, ship_upgrade):
        """
        Apply an upgrade to our ship, copy the object, and bind it to our ship object.
        
        :param ship_upgrade: 
        :return: 
        """
        pass

    def can_install_upgarde(self, ship_upgrade):
        """
        Can we apply this upgrade? We check:
        
          - max upgrade capacity
          - cost
          
        :param ship_upgrade: 
        :return: 
        """
        pass

    def get_cargo_from_good(self, good):
        """
        Given a good, get the equivalent ships cargo.
        :param good:
        :return:
        """
        return self.cargo.filter(name=good.name).first()

    def current_range(self):
        """
        How far could this ship go right now?

        :return:
        """
        print "max range(%f) * fuel level(%f) / 100.0" % (self.max_range, self.fuel_level)
        return self.max_range * (self.fuel_level / 100.0)

    def has_in_cargo(self, good):
        """
        Does the ship have any of this good in cargo?

        :return:
        """
        cargo = self.cargo.filter(name=good.name).first()

        if cargo is None:
            return False
        elif cargo.quantity == 0:
            return False
        else:
            return True

    def quantity_in_cargo(self, good):
        """
        How much of this good do we have in cargo?

        :return:
        """
        cargo = self.cargo.filter(name=good.name).first()

        if cargo is None:
            return 0
        else:
            return cargo.quantity

    def cargo_used(self):
        """
        What's the size of our currently used cargo?
        :return:
        """

        # add up all of our cargo
        cargo_count = 0

        for c in self.cargo.only("quantity").all():
            cargo_count += c.quantity
        return cargo_count

    def cargo_free(self):
        """
        What's the free space in our cargo bay?

        :return:
        """
        return self.cargo_capacity - self.cargo_used()

    def cargo_load_percent(self):
        """
        What percent of our cargo hold is filled?

        :return:
        """
        return self.cargo_used() * 1.0 / self.cargo_capacity * 100.0

    def sell_cargo(self, good, quantity):
        """
        Let's sell some things. We need to:

            1. Determine if we have any of this good
            2. If we do, make sure we have enough to sell
            3. Subtract from cargo
            4. If cargo type is empty, delete it

        :param good:
        :param quantity:
        :return:
        """
        cargo = self.cargo.filter(name=good.name).first()

        # do we even have this?
        if cargo is None:
            return

        # do we have enough to sell
        if quantity > cargo.quantity:
            return

        # great, let's sell
        cargo.sell(good, quantity)

        # is this cargo empty?
        if cargo.quantity == 0:
            cargo.delete()

    def buy_cargo(self, good, quantity):
        """
        Let's buy some goods. We need to:

            1. Determine if we already have some of this good
            2. Determine if we have space for this good
            3. If we don't have this good, add it to our cargo
            4. Use the cargo buy method to update the cargo

        :param good:
        :param quantity:
        :return:
        """

        # do we have space?
        if quantity > self.cargo_free():
            return

        # grab it if we've got it
        cargo = self.cargo.filter(name = good.name).first()

        # doesn't exist? Let's add it
        if cargo is None:
            cargo = Cargo.objects.create(
                ship = self,
                name = good.name
            )
            cargo.save()

        # great, now let's buy
        cargo.buy(good, quantity)

        # neat. done.

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
