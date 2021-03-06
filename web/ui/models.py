from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.contrib.postgres.fields import JSONField

import random
import string
import json
import os
import math


# LOCATION CONTROLS

## Images

# Planets
planet_range = range(1,8) + range(10, 21)
PLANET_IMAGES = ["planet%d.png" % i for i in planet_range]

# Stars
STAR_IMAGES = [star for star in os.listdir("ui/static/ui/images/stars") if star.endswith("png")]

# Nebula
NEBULA_IMAGES = [n for n in os.listdir("ui/static/ui/images/nebulas") if n.endswith("png")]

# SHIP Images
SHIP_IMAGES = [ship for ship in os.listdir("ui/static/ui/images/ships") if ship.endswith("png")]

# Asteroid Images
ASTEROID_IMAGES = [a for a in os.listdir("ui/static/ui/images/asteroids") if a.endswith("png")]

# Moon Images
MOON_IMAGES = [m for m in os.listdir("ui/static/ui/images/moons") if m.endswith("png")]

## Names

# Star/Planet System name prefixes
with open("ui/resources/planet_prefix.list", "r") as prefixes:
    SYSTEM_PREFIXES = [prefix.strip() for prefix in prefixes.readlines()]

# What kind of locations do we have?
LOCATION_CHOICES = (
    ("planet", "Planet"),
    ("star", "Star"),
    ("moon", "Moon"),
    ("asteroid", "Asterpid"),
    ("nebula", "Nebula")
)


## Procedural Generation Settings

# Shipyards
SHIPYARDS = json.load(open("ui/resources/shipyards.json", "r"))

# Ship types
SHIP_TEMPLATES = json.load(open("ui/resources/shiptypes.json", "r"))

# LOAD THE GOODS!
GOODS = json.load(open("ui/resources/goods.json", "r"))

# What are our upgrade qualities?
UPGRADES = json.load(open("ui/resources/upgrades.json", "r"))

## Runtime Configuration

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
# Locations
###
class LocationManager(models.Manager):
    """
    Query, build, and otherwise manipulate the different Location types.
    """

    def delete_unoccupied(self):
        """
        Delete any locations that don't have a player in orbit.

        :return:
        """
        self.exclude(orbiters__owner__isnull=False).exclude(registrants__owner__isnull=False).delete()

    def pick_random(self):
        """
        Pick a random location that we already have available.

        :return:
        """
        id = random.sample(self.only("id").all(), 1)
        return id[0]

    def create_random(self, has_shipyard=True, has_marketplace=True):
        """
        Create and place a random Location. This Location generator is
        not context sensitive to location type - it just scatters things
        all about.

        :return:
        """

        # coordinates
        x_co = random.randrange(-1000, 1000)
        y_co = random.randrange(-1000, 1000)

        # what type of location are we?
        location_type = random.sample(LOCATION_CHOICES, 1)[0][0]

        print "%% LocationManager::create_random - generating a %s" % (location_type,)
        # let's figure out what we are, shall we?
        location_name = ""
        location_image = ""

        if location_type == "planet":

            # now we need a name
            location_name = self.random_planet_name()

            # we also need to pick out an image
            location_image = random.sample(PLANET_IMAGES,1)[0]

        elif location_type == "moon":

            # we'll use satellite provisional naming ( https://en.wikipedia.org/wiki/Naming_of_moons#Provisional_designations )
            m_year = random.randrange(2010, 10000)
            m_plan = random.choice("ABCDEFGHJKLMNO[QRSTUVWXYZ")
            m_inc = random.randrange(1, 1000)

            location_name = "S/%d %s %d" % (m_year, m_plan, m_inc)

            # grab our image
            location_image = random.sample(MOON_IMAGES, 1)[0]

        elif location_type == "asteroid":

            # Asteroids use New-style Provisional Naming ( https://en.wikipedia.org/wiki/Provisional_designation_in_astronomy )
            ast_year = random.randrange(2010, 10000)
            ast_la = random.choice("ABCDEFGHJKLMNOPQRSTUVWXY")
            ast_lb = random.choice("ABCDEFGHJKLMNO[QRSTUVWXYZ")
            ast_cy = random.randrange(1,500)

            location_name = "%d %s %s-%d" % (ast_year, ast_la, ast_lb, ast_cy)

            # we also need to pick out an image
            location_image = random.sample(ASTEROID_IMAGES, 1)[0]

        elif location_type == "nebula":

            # Nebulas are going with NGC names for now
            location_name = "NGC %d" % (random.randrange(10,10000))

            # we also need to pick out an image
            location_image = random.sample(NEBULA_IMAGES, 1)[0]

        elif location_type == "star":

            # pick a star name
            location_name = self.random_star_name()

            # pick a star, any star
            location_image = random.sample(STAR_IMAGES, 1)[0]
        else:
            print "! Generator Error [models::LocationManager::create_random] - No idea how to create a random [%s]" % (location_type,)

        # make our planet
        obj = self.create(
            name = location_name,
            location_type = location_type,

            x_coordinate = x_co,
            y_coordinate = y_co,

            image_name = location_image
        )

        # only a few places actually have imports and exports, so we'll
        # filter here
        if location_type in ["planet", "moon", "asteroid"]:

            # let's add some imports
            num_imports = random.randint(3, 6)
            ims = random.sample(GOODS, num_imports)
            for im in ims:
                candidate = random.random()
                if candidate >= im["liklihood"]["import"]:
                    p_import = Good.objects.create(
                        location = obj,
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
                        location = obj,
                        name = im["good"],
                        is_import = False,
                        is_export = True,
                        price = random.uniform(im["price"]["export"]["min"], im["price"]["export"]["max"]) * im["price"]["base"]
                    )

        # do we have a shipyard?
        if has_shipyard:
            yard = ShipYard.objects.create_random_on_location(obj)

        return obj

    def random_planet_name(self):
        """
        Generate a random planet name.

        :return:
        """

        # get a good prefix
        planet_prefix = random.sample(SYSTEM_PREFIXES, 1)[0]

        # pick a designator
        planet_number = random.randint(1000, 10000)

        # system location?
        planet_orbit = random.sample(string.ascii_uppercase, 1)[0]

        return "%s %d-%s" % (planet_prefix, planet_number, planet_orbit)

    def random_star_name(self):
        """
        Generate a random name for a star. This shares generation ideas
        with random_planet_name.

        :return:
        """
        # get a good prefix
        star_prefix = random.sample(SYSTEM_PREFIXES, 1)[0]

        # pick a designator
        star_number = random.randint(1000, 10000)

        return "%s %s" % (star_prefix, star_number)


def default_location_meta():
    """
    Default data for a location's metadata.

    :return:
    """
    return {}


class Location(models.Model):
    """
    Describe a Location.
    """
    objects = LocationManager()

    name = models.CharField(max_length=255, null=False, blank=False)

    # where is this location?
    x_coordinate = models.IntegerField(default=0, null=False, blank=False)
    y_coordinate = models.IntegerField(default=0, null=False, blank=False)

    # some display settings
    image_name = models.CharField(max_length=255, null=False, blank=False)

    # rarity of fuel effects the overall refueling cost. This is some sane number
    # basically [50% - 200%] of standard price
    fuel_markup = models.FloatField(default=1.0)

    # What kind of location is this?
    location_type = models.CharField(max_length=255, null=False, blank=False, choices=LOCATION_CHOICES, default="planet")

    # what features does this location have?
    location_meta = JSONField(null=False, blank=False, default=default_location_meta)

    # does this location have a parent location?
    parent = models.ForeignKey("Location", null=True)

    # location hash let's us grab a whole set of related locations in a single query
    location_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)

    def imports(self):
        return self.goods.filter(is_import=True)

    def exports(self):
        return self.goods.filter(is_export=True)

    def add_shipyard(self):
        """
        Create a shipyard on our location.
        
        :return: 
        """
        ShipYard.objects.create_random_on_location(self)

    def static_suffix(self):
        """
        What is the location of this in the static content?

        :return:
        """
        return "ui/images/%ss/%s" % (self.location_type, self.image_name)


###
# GOODS
###
class Good(models.Model):
    """
    An instance of a good or service, linked to a location or a Ship.
    """

    name = models.CharField(max_length=255, null=False, blank=False)

    # what location has these goods?
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="goods")

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
    return Location.objects.first()


class ShipManager(models.Manager):
    """
    Work with ships.
    """

    def __choose_ship_stats(self):
        """
        Use our stats in the shiptypes.json to build the
        basic features of a ship. We return a dict that
        can be used to seed a ship object.
        
        We use a quasi-monte-carlo method here:
            
            1. Randomly choose a ship type
            2. Randomly choose candidate number C
            3. If C is <= random ship availability, continue with ship
            4. goto 1
        
        when we have a ship template from 3, we then random choose
        values from the:
            
            - range
            - cargo
            - upgrade
        
        And use the shiptypes entries for each of the `sizes` to
        calculate the size of each value, as well as the overall
        cost of the ship.
        
        :return: 
        """

        # find a good ship template
        have_template = False
        template = None

        while not have_template:

            template_candidate = random.choice(SHIP_TEMPLATES["ships"])
            mc_candidate = random.random()

            if mc_candidate <= template_candidate["availability"]:
                have_template = True
                template = template_candidate

        # do some basic selections from our possible settings
        range_data = SHIP_TEMPLATES["sizes"][random.choice(template["range"])]
        cargo_data = SHIP_TEMPLATES["sizes"][random.choice(template["cargo"])]
        upgrade_data = SHIP_TEMPLATES["sizes"][random.choice(template["upgrade"])]

        # do some cost coversions and build our template
        price_factor = range_data["cost"] + cargo_data["cost"] + upgrade_data["cost"]

        return {
            "name": template["name"],
            "description": template["description"],
            "max_range": range_data["size"] * 5,
            "cargo_capacity": cargo_data["size"],
            "upgrade_capacity": upgrade_data["size"],
            "cost": ( 2 ** price_factor) * 250
        }

    def seed_ship_for_profile(self, profile):
        """
        Generate a ship for the given profile (could be user or NPC).

        :param profile:
        :return:
        """
        # what location is this?
        location = Location.objects.pick_random()

        # get our template
        ship_template = self.__choose_ship_stats()

        # set up all of the various variables we'll use in
        # model construction
        ship_name = ship_template["name"]
        ship_model = ship_template["name"]
        ship_location = location
        ship_home_location = location
        ship_range = ship_template["max_range"]
        ship_fuel_level = 100.0
        ship_cargo_capacity = ship_template["cargo_capacity"]
        ship_upgrade_capacity = ship_template["upgrade_capacity"]
        ship_image = random.sample(SHIP_IMAGES, 1)[0]
        ship_value = ship_template["cost"]

        ship = self.create(
            name = ship_name,
            model = ship_model,
            location = ship_location,
            home_location = ship_home_location,
            max_range = ship_range,
            fuel_level = ship_fuel_level,
            cargo_capacity = ship_cargo_capacity,
            upgrade_capacity = ship_upgrade_capacity,
            image_name = ship_image,
            value = ship_value,
            owner = profile
        )

        return ship

    def seed_ship_at_shipyard(self, shipyard):
        """
        Generate a ship at the shipyard.
        
        :param shipyard: 
        :return: 
        """

        # what location is this?
        location = shipyard.location

        # get our template
        ship_template = self.__choose_ship_stats()

        # set up all of the various variables we'll use in
        # model construction
        ship_name = ship_template["name"]
        ship_model = ship_template["name"]
        ship_location = location
        ship_home_location = location
        ship_range = ship_template["max_range"]
        ship_fuel_level = 100.0
        ship_cargo_capacity = ship_template["cargo_capacity"]
        ship_upgrade_capacity = ship_template["upgrade_capacity"]
        ship_image = random.sample(SHIP_IMAGES, 1)[0]
        ship_value = ship_template["cost"]

        ship = self.create(
            name = ship_name,
            model = ship_model,
            location = ship_location,
            home_location = ship_home_location,
            max_range = ship_range,
            fuel_level = ship_fuel_level,
            cargo_capacity = ship_cargo_capacity,
            upgrade_capacity = ship_upgrade_capacity,
            image_name = ship_image,
            value = ship_value,
            shipyard = shipyard
        )

        return ship


class ShipUpgradeManager(models.Manager):
    """
    Manage how we generate new ship upgrades, using the UPGRADES data.
    """

    def upgrade_quality_blurb(self):
        """
        Build a text blurb describing our upgrades.
        
        :return: 
        """
        blurb = "<ul>"
        for upgrade in UPGRADES["grades"]:
            blurb += "<li> <strong>%s</strong> - <em>Also known as %s grade.</em> %s</li>" % (upgrade["name"], upgrade["id"], upgrade["description"])
        blurb += "</ul>"
        return blurb

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
                    print json.dumps(component)
                    print json.dumps(grade)
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

    def too_few_ships_available(self):
        """
        Find ship yards with an insufficient number of ships available.

        :return: QuerySet of ShipYard objects
        """
        return self.annotate(ship_count=models.Count('ships')).filter(ship_count__lt=3)

    def create_random_on_location(self, location):
        """
        Generate a new ship yard.
        
        We use:
        
         - SHIPYARDS::names - Data for generating ship yard names
        
        :return: 
        """
        yard = self.create(
            name=self._create_name(),
            location=location
        )
        yard.save()

        # seed upgrades
        yard.seed_upgrades()

        # seed ships
        yard.seed_ships(3)

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
    Some locations have ship yards. Ship yards hold upgrades and ships for purchase.
    """
    objects = ShipYardManager()

    # descriptive name of the shipyard
    name = models.CharField(max_length=255, blank=False, null=False)

    # what location does this belong on?
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="shipyards")

    def name_display(self):
        """
        Turn the name into a better format for display.
        
        :return: 
        """
        return " ".join([word.capitalize() for word in self.name.split(" ")])

    def upgrades_by_cost(self):
        """
        Sort the upgrades by ascending cost, and return the queryset.
        
        :return: 
        """
        return self.upgrades.order_by("cost")

    def ships_by_cost(self):
        """
        Sort the available ships at this yard by cost, and return the queryset.
        
        :return: 
        """
        return self.ships.order_by("value")

    def seed_upgrades(self):
        """
        Setup the upgrades available at a ShipYard.
        
        :return: 
        """

        # get our upgrades
        upgrades = ShipUpgrade.objects.create_cargo_upgrades()

        # add them to our shipyard
        for upgrade in upgrades:
            upgrade.shipyard = self
            upgrade.save()

        print "Seeded shipyard [%s] with %d upgrades" % (self.name, len(upgrades))

    def restock_upgrades(self, quantity=None):
        """
        Restock the supply of upgrades. If the incoming
        quantity is None, we'll randomly add 1d6 items.
        
        :return: 
        """

        if quantity is None:
            quantity = random.choice([1,2,3,4,5,6])

        for x in range(quantity):
            upgrade = ShipUpgrade.objects.create_cargo_upgrade()
            upgrade.shipyard = self
            upgrade.save()

    def seed_ships(self, quantity=1):
        """
        What ships are available for purchase?
        
        :return: 
        """

        for x in range(quantity):
            Ship.objects.seed_ship_at_shipyard(self)


    def restock_ships(self, up_to=3):
        """
        What ships are availale for purchase?
        
        :return: 
        """
        current_count = self.ships.count()

        for nc in range(up_to-current_count):
            Ship.objects.seed_ship_at_shipyard(self)

        return up_to - current_count

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
    ship = models.ForeignKey("Ship", blank=True, null=True, on_delete=models.CASCADE, related_name="upgrades")

    # what did this upgrade cost
    cost = models.BigIntegerField(null=False, blank=False, default=100000)

    # what do we call this?
    name = models.CharField(max_length=255, null=False, blank=False)

    # what quality is this upgrade?
    quality = models.CharField(max_length=10, null=False, blank=False)

    # how much upgrade capacity does this take up?
    capacity = models.IntegerField(null=False, blank=False, default=10)

    # do we have a description?
    description = models.TextField(null=True, blank=True)

    # which shipyard is this upgrade stocked at?
    shipyard = models.ForeignKey("ShipYard", blank=True, null=True, on_delete=models.CASCADE, related_name="upgrades")

    def buy(self):
        """
        We've been purchased!
        
        We need to remove our self from the shipyard. We'll also tell the yard to restock
        an item(s).
        
        :return: 
        """
        yard = self.shipyard

        # let our shipyard know
        yard.restock_upgrades()

        # we're no longer for purchase!
        self.shipyard = None
        self.save()



def default_ship_computer():
    """
    Build the default ships computer structure.
    
    Fields:
        
        limits.travel.history: ships memory for past travel
        limits.cargo.history: ships memory for past cargo transactions
        travel.history: fifo, head oriented list of most recent travel `limits.history.travel` defines max length
        cargo.history:: fifo, head oriented list of recent cargo manifest changes `limits.cargo.history` defines max length
        
    Field content descriptions:
    
        travel.history:
            
            {
                "name": "Planet Name"
                "id": <integer>Planet ID
                "x_coordinate": <integer>
                "y_coordinate": <integer>
            }

        cargo.history:

            {
                "mode": buy | sell,
                "good": <string>,
                "quantity": <integer>,
                "planet": {
                    "name": planet.name,
                    "id": planet.id
                },
                "cost": <integer>
            }

    :return: 
    """
    return {
        "limits": {
            "travel": {
                "history": 5
            },
            "cargo":{
                "history": 5
            }
        },
        "travel": {
            "history": []
        },
        "cargo": {
            "history": []
        }
    }


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

    # a ship is at a location
    location = models.ForeignKey(Location, null=False, blank=False, on_delete=models.CASCADE, related_name="orbiters")

    # a ship also has a home location
    home_location = models.ForeignKey(Location, null=False, blank=False, on_delete=models.CASCADE, related_name="registrants")

    # some basic settings that we'll improve upon later

    # how far can we go on a full tank?
    max_range = models.IntegerField(null=False, blank=False, default=1000)

    # for now we'll treat fuel as a perentage of a tank of fuel
    fuel_level = models.FloatField(null=False, blank=False, default=100.0)

    # how much cargo space do we have?
    cargo_capacity = models.IntegerField(null=False, blank=False, default=50)

    # how much of our upgrade space do we have?
    upgrade_capacity = models.IntegerField(null=False, blank=False, default=0)

    # image for this ship?
    image_name = models.CharField(max_length=255, null=False, blank=False)

    # what yard, if any, is this ship at?
    shipyard = models.ForeignKey("ShipYard", null=True, blank=True, related_name="ships")

    # ships computer, tracks features of the ship
    computer = JSONField(null=False, blank=False, default=default_ship_computer)

    def upgrade_size_cargo(self):
        """
        How much bigger is our cargo with installed upgrades.
        
        :return: 
        """
        size = self.upgrades.only("size").filter(target="cargo").aggregate(models.Sum("size"))["size__sum"]
        if size is None:
            size = 0
        return size

    def upgrade_capacity_used(self):
        """
        Determine how much of our upgrade capacity is already used.
        
        :return: 
        """
        used = self.upgrades.only("capacity").aggregate(models.Sum("capacity"))["capacity__sum"]
        if used is None:
            used = 0
        return used

    def upgrade_capacity_free(self):
        """
        How much upgrade capacity do we have left?
        
        :return: 
        """
        return self.upgrade_capacity - self.upgrade_capacity_used()

    def upgrade_load_percent(self):
        """
        Return a 100 shifted percent value of currently used upgrade capacity.
        
        :return: 
        """
        numer = self.upgrade_capacity_used()
        denom = self.upgrade_capacity

        if denom == 0:
            return 0
        else:
            return (numer * 1.0) / denom * 100.0

    def buy_upgrade(self, ship_upgrade):
        """
        A few things we need to do when buying an upgrade:
        
            1. Can we install it?
            2. Install it
            3. Use ShipUpgrade::buy to complete the transaction
            
        :param upgrade: 
        :return: 
        """

        # enough space for it?
        if not self.can_install_upgrade(ship_upgrade):
            return

        # ok - let's do this.

        #  - install
        self.install_upgrade(ship_upgrade)

        #  - buy it
        ship_upgrade.buy()

        # we're good.


    def install_upgrade(self, ship_upgrade):
        """
        Apply an upgrade to our ship, copy the object, and bind it to our ship object.
            
            1. set ship of ship_upgrade
            2. update proper component value of ship. From ShipUpgrade:
            
                # how much does this change our ship
                size = models.IntegerField(null=False, blank=False, default=10)
                
                # what on our ship does this change?
                target = models.CharField(max_length=100, null=False, blank=False, default="cargo")

            
        :param ship_upgrade: 
        :return: 
        """

        # it's ours!
        ship_upgrade.ship = self
        ship_upgrade.save()

        # let's do some install
        if ship_upgrade.target == "cargo":
            self.cargo_capacity += ship_upgrade.size
            self.save()

    def can_install_upgrade(self, ship_upgrade):
        """
        Can we apply this upgrade? We check:
        
          - max upgrade capacity
          
        :param ship_upgrade: 
        :return: 
        """

        if ship_upgrade.capacity > self.upgrade_capacity_free():
            return False

        return True

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

        # neat. done. let's record this for posterity
        self.record_cargo_sell(good, quantity, good.location, good.price * quantity)

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

        # neat. done. let's record this for posterity
        self.record_cargo_buy(good, quantity, good.location, good.price * quantity)

    def locations_in_range(self):
        """
        Find the locations that are in range, and compute a bit of data
        :return:
        """
        plist = []

        # figure out how far we can go
        max_range = self.current_range()

        # bail out if we're reaaaaaally low on fuel
        if max_range < 1:
            return plist

        # preselect a set of locations in the box that our max range describes
        min_x = self.location.x_coordinate - max_range
        max_x = self.location.x_coordinate + max_range
        min_y = self.location.y_coordinate - max_range
        max_y = self.location.y_coordinate + max_range

        close_enough = Location.objects.filter(
            x_coordinate__gte=min_x,
            x_coordinate__lte=max_x,
            y_coordinate__gte=min_y,
            y_coordinate__lte=max_y
        ).all()

        for location in close_enough:

            # now do a real distance calculation
            real_dist = self.distance_to(location)
            if real_dist > self.current_range():
                continue

            # ok! our location is close enough
            plist.append(
                {
                    "name": location.name,
                    "id": location.id,
                    "distance": real_dist,
                    "fuel_burned_percent": real_dist / max_range * 100.0,
                    "location_type": location.location_type
                }
            )
        plist.sort(key=lambda s: s["distance"])

        return plist

    def distance_to(self, location):
        """
        How far is it to the given location.

        :param location:
        :return:
        """
        return math.sqrt(((self.location.x_coordinate - location.x_coordinate)**2) + ((self.location.y_coordinate - location.y_coordinate)**2))

    def record_cargo_buy(self, good, quantity, location, cost):
        """
        Add a record to our cargo log.
        
        :param good: 
        :param quantity: 
        :param location:
        :param cost: 
        :return: 
        """
        self._record_cargo("buy", good, quantity, location, cost)

    def record_cargo_sell(self, good, quantity, location, cost):
        """
        Add a record to our cargo log.
            
        :param good: 
        :param quantity: 
        :param location:
        :param cost: 
        :return: 
        """
        self._record_cargo("sell", good, quantity, location, cost)

    def _record_cargo(self, mode, good, quantity, location, cost):
        """
        Add a record to our cargo log, and trim it down if need be. 
         
        :param mode: 
        :param good: 
        :param quantity: 
        :param plant: 
        :param cost: 
        :return: 
        """
        rec = {
            "mode": mode,
            "good": good.name,
            "quantity": quantity,
            "planet": {
                "name": location.name,
                "id": location.id
            },
            "cost": cost
        }
        self.computer["cargo"]["history"].insert(0, rec)
        self.computer["cargo"]["history"] = self.computer["cargo"]["history"][:self.computer["limits"]["cargo"]["history"]]
        self.save()

    def travel_to(self, location):
        """
        Update the ship for travel to a location. We're going to save our travel history
        as we go.
        

        :param location:
        :return:
        """

        # update our travel history
        last_location = {
            "name": self.location.name,
            "id": self.location.id,
            "x_coordinate": self.location.x_coordinate,
            "y_coordinate": self.location.y_coordinate
        }
        self.computer["travel"]["history"].insert(0,last_location)
        self.computer["travel"]["history"] = self.computer["travel"]["history"][:self.computer["limits"]["travel"]["history"]]

        # travel
        self.location = location
        self.save()

    def is_home_location_in_range(self):
        """
        Is our home location within travel distance?

        :return:
        """
        return self.current_range() > self.distance_to(self.home_location)

    def is_home(self):
        return self.location == self.home_location

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
        What's the cost to refuel on our current location? We need to take
        into account the possibility of not having enough money to fully
        refuel.

        :return:
        """

        # how many units of fuel do we need
        f_used, f_available = self.fuel_units()

        # given the location markup, what will our used fuel cost to
        # replace?
        cost = FUEL_UNIT_COST * self.location.fuel_markup * f_used
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
