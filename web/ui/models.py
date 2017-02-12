from __future__ import unicode_literals

from django.db import models

import random
import string
import json

# the goods we use on planets and ships
# LOAD THE GOODS!
GOODS = json.loads(open("ui/resources/goods.json", "r").read())

# What are our planet images?
PLANET_IMAGES = ["planet%d.png" % i for i in range(1,21)]

class PlanetManager(models.Manager):
    """
    Query, build, and otherwise manipulate Planets.
    """

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

    def imports(self):
        return self.goods.filter(is_import=True)

    def exports(self):
        return self.goods.filter(is_export=True)


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
