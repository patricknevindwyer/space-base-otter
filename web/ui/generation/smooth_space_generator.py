import argparse
from collections import namedtuple
import hashlib
import json
import math
from opensimplex import OpenSimplex
import os
import random
import string
import sys

"""
The *smooth_space_generator* builds out a mostly logical galaxy sector. Inputs can include
a sector offset, random sampling offsets, and other components.

The generator returns a series of JSON structures representing all of the location objects.

Locations linked together are given internal ID references that are scoped to this generation
session. These internal IDs can be used to map the resulting objects together in the actual
Model objects.

The coordinate space used by the smooth generator pins (0,0) to the south west corner of
a sector, and (width, height) to the north east corner.

Every location generated by the smooth_space_generator will have a structure like:

    {
        "name"          : string name
        "x_coordinate"  : integer
        "y_coordinate"  : integer
        "image_name"    : see *_IMAGES in models.py
        "fuel_markup"   : percentage fuel markup at location, in 1.05 form (for 5% markup)
        "type" : [planet, star, asteroid, moon, nebula]
        "location_meta" : JSON metadata for the location
        "location_hash" : shared hash for related entities
        "parent_offset" : distance from parent object, in AU 
        "children"      : list of child objects
    }
    
The location_meta has the form:
    
    {
        "resources":[]
    }
"""

####
# Resource Loads
####

# Star/Planet System name prefixes
with open("ui/resources/planet_prefix.list", "r") as prefixes:
    SYSTEM_PREFIXES = [prefix.strip() for prefix in prefixes.readlines()]


####
# Images
####
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


####
# Data Structures
####

# Tuples we'll be using for data concise structures
Subsector = namedtuple("Subsector", ["subsector_row", "subsector_col", "relative", "absolute"])
SubsectorLocation = namedtuple("SubsectorLocation", ["center", "corners"])
SubsectorCorners = namedtuple("SubsectorCorners", ["nw", "ne", "sw", "se"])
Coordinate = namedtuple("Coordinate", ["x", "y"])

class SectorGenerator(object):
    """
    Handle generation control and synthesis for the smooth generator
    """

    def __init__(self):
        """
        Setup our defaults
        """
        self.locations = []

        # anchor this sector in space
        self.sector_x = 0
        self.sector_y = 0
        self.sector_width = 1000
        self.sector_height = 1000

        # how do we want to sub divide our space?
        self.x_subsectors = 10
        self.y_subsectors = 10

        # how dense is our universe? This number is used to scale the
        # relative quantity of the different features. This needs to
        # be a number from 0.0 to 1.0
        self.density = 0.6

        # noise generation and configuration.
        #
        #   **noise exponent** is used to push our noise ceiling and floor to the extremes.
        #
        #   **simplex_seed** is our configuration input to the OpenSimplex function
        #
        #   **coordinate_dampening** shrinks the coordinate space fed into simplex, making smooth transitions
        #      much cleaner and easier to notice

        self.noise_exponent = 1.05  # 1.14
        self.simplex_seed = 7222007
        self.coordinate_dampening = 500.0
        self.simplex = OpenSimplex(seed=self.simplex_seed)

    def reseed(self, seed):
        """
        Seed the simplex generator, and setup the gen function
        :param seed:
        :return:
        """
        self.simplex_seed = seed
        self.simplex = OpenSimplex(seed=self.simplex_seed)

    def noise_at_coordinate(self, coord):
        """
        Use our scaled simplex noise function to generate a random
        number between [0,1]. The coordinate used for generator should
        be the absolute universe coordinate, not a sector relative
        coordinate.

        :param coord:
        :return:
        """

        # sample at this location
        raw_noise = self.simplex.noise2d(x=coord.x/self.coordinate_dampening, y=coord.y/self.coordinate_dampening)

        # rescale
        scaled_noise = (raw_noise + 1.0) / 2.0

        # exponentiate
        exp_noise = math.pow(scaled_noise, self.noise_exponent)

        return exp_noise

    def feature_from_noise(self, noise_val):
        """
        What kind of feature is at this noise value? It's a sliding
        feature scale.

            [0.0 - 0.4) - Void
            [0.4 - 0.6) - Nebula
            [0.6 - 0.8) - Star
            [0.8 - 1.0] - Asteroid

        :param coord:
        :param noise_val:
        :return:
        """

        # bp is for break point...
        # we use our density function to determine our breakpoints. We pull apart how
        # dense the individual features are, and then whatever is left over is
        # all part of the void
        scaled_density = (1.0 / 3.0) * self.density
        void_density = 1.0 - (scaled_density * 3.0)

        bp = [
            0.0,
            void_density,
            void_density + scaled_density * 1,
            void_density + scaled_density * 2]

        if   bp[0] <= noise_val < bp[1]:
            return "void"
        elif bp[1] <= noise_val < bp[2]:
            return "nebula"
        elif bp[2] <= noise_val < bp[3]:
            return "star"
        elif bp[3] <= noise_val:
            return "asteroid"

    def subsector_iterator(self):
        """
        We know how many subsectors we want, and our general scale,
        and with this iterator we'll walk the coordinate spaces we
        want, returning some useful values for each sector:

            {
                subsector_row = #
                subsector_col = #
                relative: {
                    center: {
                        x
                        y
                    }
                    corners: {
                        nw: {
                            x
                            y
                        }
                        ne: {
                            x
                            y
                        }
                        se: {
                            x
                            y
                        }
                        sw: {
                            x
                            y
                        }
                    }
                }
                absolute: { similar values to 'relative' but in absolute coordinate space of the entire universe}
            }

        Keep in mind that our values can be negative.

        :return:
        """

        for ss_y in range(0, self.y_subsectors):
            # find our south anchor
            y_south = (self.sector_height / self.y_subsectors) * ss_y
            y_north = y_south + (self.sector_height / self.y_subsectors)
            y_center = (y_north - y_south) / 2 + y_south

            for ss_x in range(0, self.x_subsectors):

                # find our west anchor
                x_west = (self.sector_width / self.x_subsectors) * ss_x
                x_east = x_west + (self.sector_width / self.x_subsectors)
                x_center = (x_east - x_west) / 2.0 + x_west


                # now let's do some combining!
                yield Subsector(
                    subsector_row = ss_y,
                    subsector_col = ss_x,
                    relative = SubsectorLocation(
                        center = Coordinate(
                            x = x_center,
                            y = y_center
                        ),
                        corners = SubsectorCorners(
                            nw = Coordinate(
                                x = x_west,
                                y = y_north
                            ),
                            ne = Coordinate(
                                x = x_east,
                                y = y_north
                            ),
                            se = Coordinate(
                                x = x_east,
                                y = y_south
                            ),
                            sw = Coordinate(
                                x = x_west,
                                y = y_south
                            )
                        )
                    ),
                    absolute = SubsectorLocation(
                        center = Coordinate(
                            x = x_center + self.sector_x,
                            y = y_center + self.sector_y
                        ),
                        corners = SubsectorCorners(
                            nw = Coordinate(
                                x = x_west + self.sector_x,
                                y = y_north + self.sector_y
                            ),
                            ne = Coordinate(
                                x = x_east + self.sector_x,
                                y = y_north + self.sector_y
                            ),
                            se = Coordinate(
                                x = x_east + self.sector_x,
                                y = y_south + self.sector_y
                            ),
                            sw = Coordinate(
                                x = x_west + self.sector_x,
                                y = y_south + self.sector_y
                            )
                        )
                    )
                )


class NebulaGenerator(object):
    """
    Generate a Nebula. Each nebula has a certain set of resources, which we generate
    at creation time.
    """

    def __init__(self):
        """
        Setup general nebula generation
        """
        pass

    def create_at_location(self, x, y):
        """
        Generate a nebula at the given location.

        :param x:
        :param y:
        :return:
        """
        return {
            "name": self._create_name(),
            "x_coordinate": x,
            "y_coordinate": y,
            "type": "nebula",
            "location_hash": create_location_hash(x, y),
            "image_name": random.sample(NEBULA_IMAGES, 1)[0],
            "fuel_markup": 1.0,
            "location_meta": {}
        }

    def _create_name(self):
        """
        Simple name generation for Nebulas.

        :return:
        """
        return "NGC %d" % (random.randrange(10, 10000))


class MoonGenerator(object):
    """
    Generator for moons.
    """

    def __init__(self):
        """
        setup moon generation.
        """
        self.location_hash = None
        self.parent_offset = 0

    def with_location_hash(self, location_hash):
        """
        Create planets with the given shared location hash.

        :param location_hash:
        :return:
        """
        self.location_hash = location_hash

    def at_parent_offset(self, parent_offset_au):
        """
        How far from the parent object, in Astronomical Units, is this object?

        :param parent_distance_au:
        :return:
        """
        self.parent_offset = parent_offset_au

    def create_at_location(self, x, y):
        """
        Create a moon at the given location.

        :param x:
        :param y:
        :return:
        """
        return {
            "name": self._create_name(),
            "x_coordinate": x,
            "y_coordinate": y,
            "location_hash": self.location_hash,
            "parent_offset": self.parent_offset,
            "type": "moon",
            "image_name": random.sample(MOON_IMAGES, 1)[0],
            "fuel_markup": 1.0,
            "location_meta": {}
        }

    def _create_name(self):
        """
        we'll use satellite provisional naming ( https://en.wikipedia.org/wiki/Naming_of_moons#Provisional_designations )
        """
        m_year = random.randrange(2010, 10000)
        m_plan = random.choice("ABCDEFGHJKLMNO[QRSTUVWXYZ")
        m_inc = random.randrange(1, 1000)

        return "S/%d %s %d" % (m_year, m_plan, m_inc)


class PlanetGenerator(object):
    """
    Generator for planets. Each planet also generates its moons.
    """

    def __init__(self):
        """
        Setup planet generation.
        """
        self.moon_generator = MoonGenerator()
        self.location_hash = None
        self.parent_offset = 0
        self.name = ""

    def with_location_hash(self, location_hash):
        """
        Create planets with the given shared location hash.

        :param location_hash:
        :return:
        """
        self.location_hash = location_hash

    def at_parent_offset(self, parent_offset_au):
        """
        How far from the parent object, in Astronomical Units, is this object?

        :param parent_distance_au:
        :return:
        """
        self.parent_offset = parent_offset_au

    def create_at_location(self, x, y):
        """
        Generate a planet at the given location.

        :param x:
        :param y:
        :return:
        """
        return {
            "name": self.name,
            "x_coordinate": x,
            "y_coordinate": y,
            "location_hash": self.location_hash,
            "parent_offset": self.parent_offset,
            "children": self._create_moons(),
            "type": "planet",
            "image_name": random.sample(PLANET_IMAGES, 1)[0],
            "fuel_markup": 1.0,
            "location_meta": {}
        }

    def with_name(self, name):
        """
        Inherit our name

        :return:
        """
        self.name = name

    def _create_moons(self, x_coordinate=0, y_coordinate=0):
        """
        Create the moons for this planet.

        :return:
        """

        self.moon_generator.with_location_hash(self.location_hash)

        # how many moons are we creating?
        moon_count = int(random.triangular(0, 50, 7))

        # gather up all of our moons
        moons = []

        for i in range(moon_count):

            # set how far the moon will be from the planet
            self.moon_generator.at_parent_offset(random.uniform(0.001, 1.0))

            # create our moon
            moons.append(self.moon_generator.create_at_location(x_coordinate, y_coordinate))

        return moons


class AsteroidGenerator(object):
    """
    Generator for asteroids.
    """

    def __init__(self):
        """
        Setup asteroid generation.
        """
        pass

    def create_at_location(self, x, y):
        """
        Create an asteroid at the given location.

        :param x:
        :param y:
        :return:
        """
        return {
            "name": self._create_name(),
            "x_coordinate": x,
            "y_coordinate": y,
            "type": "asteroid",
            "location_hash": create_location_hash(x, y),
            "image_name": random.sample(ASTEROID_IMAGES, 1)[0],
            "fuel_markup": 1.0,
            "location_meta": {}
        }

    def _create_name(self):
        """
        Asteroids use New-style Provisional Naming ( https://en.wikipedia.org/wiki/Provisional_designation_in_astronomy )
        :return:
        """
        ast_year = random.randrange(2010, 10000)
        ast_la = random.choice("ABCDEFGHJKLMNOPQRSTUVWXY")
        ast_lb = random.choice("ABCDEFGHJKLMNO[QRSTUVWXYZ")
        ast_cy = random.randrange(1, 500)

        return "%d %s %s-%d" % (ast_year, ast_la, ast_lb, ast_cy)


class StarGenerator(object):
    """
    Generator for stars. Each star, when generated, also creates
    its planets and moons.
    """

    def __init__(self):
        """
        Setup star generation.
        """
        self.planet_generator = PlanetGenerator()

    def create_at_location(self, x, y):
        """
        Create a star, and all of its sub-objects.

        :param x:
        :param y:
        :return:
        """
        loc_hash = create_location_hash(x, y)
        name = self._create_name()
        return {
            "name": name,
            "x_coordinate": x,
            "y_coordinate": y,
            "location_hash": loc_hash,
            "children": self._create_planets(star_name=name, x_coordinate=x, y_coordinate=y, location_hash=loc_hash),
            "type": "star",
            "image_name": random.sample(STAR_IMAGES, 1)[0],
            "fuel_markup": 1.0,
            "location_meta": {}
        }

    def _create_planets(self, star_name="", x_coordinate=0, y_coordinate=0, location_hash=None):
        """
        Create a set of planets orbiting our star.

        :return:
        """

        self.planet_generator.with_location_hash(location_hash)

        # how many planets are we generating?
        planet_count = int(random.triangular(0, 20, 4))

        # We're starting with our first planet somewhere between 0.25 and 0.5 AU
        # from the parent star
        planet_au = random.uniform(0.25, 0.5)

        # the further out into the planets we get, the further apart they start to spread, with
        # our trianglular variate boundaries growing by au_slide_*
        au_slide_lower = 0.25
        au_slide_higher = 1.5

        # hold our planets
        planets = []

        # start generating
        for i in range(0, planet_count):

            # configure planet creation
            self.planet_generator.at_parent_offset(planet_au)

            # pick the planet name based upon our offset into the planet sequence, and the parent
            # star name. It's possible, though remotely so, to have more than 26 planets
            planet_suffix = ""
            ps_lead = i / 26
            ps_tail = i % 26
            if ps_lead > 0:
                planet_suffix = string.ascii_uppercase[ps_lead - 1] + string.ascii_uppercase[ps_tail]
            else:
                planet_suffix = string.ascii_uppercase[i]

            planet_name = star_name + " " + planet_suffix

            self.planet_generator.with_name(planet_name)

            # create
            planets.append(self.planet_generator.create_at_location(x_coordinate, y_coordinate))

            # update the AU offset, using a starting triangular variate between 1 and 10, with a mean of 3.
            # this number grows the further into a planet sequence we get
            au_low = 1 + au_slide_lower * i
            au_high = 10 + au_slide_higher * i
            au_mean = ((au_high - au_low) / 3.0) + au_low
            planet_au += random.triangular(au_low, au_high, au_mean)

        return planets

    def _create_name(self):
        """
        Create a name for our star
        :return:
        """
        # get a good prefix
        star_prefix = random.sample(SYSTEM_PREFIXES, 1)[0]

        # pick a designator
        star_number = random.randint(1000, 10000)

        return "%s %s" % (star_prefix, star_number)


def create_location_hash(x, y):
    """
    Generate a unique location hash that can be shared among
    related locations.

    :return:
    """
    n = hashlib.sha256()
    n.update("(%d, %d)" % (x, y))
    return n.hexdigest()


def options():
    parse = argparse.ArgumentParser(description='Interaction with smooth_space_generator')

    parse.add_argument("--sector", action="store_const", const="sector", dest="action", help="Generate a sub-sector map")
    parse.add_argument("--star", action="store_const", const="star", dest="action", help="Generate a star")
    parse.add_argument("--nebula", action="store_const", const="nebula", dest="action", help="Generate a nebula")
    parse.add_argument("--asteroid", action="store_const", const="asteroid", dest="action", help="Generate an asteroid")

    parse.add_argument("--x", dest="x_coordinate", type=int, default=0, help="X Coordinate for generation")
    parse.add_argument("--y", dest="y_coordinate", type=int, default=0, help="Y Coordinate for generation")

    return parse.parse_args()


def cli_sector(opts):
    """
    Generate a sub-sector.

    :param opts:
    :return:
    """
    # assume our sector x and y at (0,0)
    sector_x = 0
    sector_y = 0

    if len(sys.argv) > 2:
        sector_y = int(sys.argv[-1])
        sector_x = int(sys.argv[-2])

    # setup a generator
    generator = SectorGenerator()

    generator.sector_y = sector_y
    generator.sector_x = sector_x

    for subsector in generator.subsector_iterator():

        # setup our row dividers
        if subsector.subsector_col == 0:
            print "|",

        # format our row
        noise = generator.noise_at_coordinate(subsector.absolute.center)
        feature = generator.feature_from_noise(noise)[0]
        if feature == "v":
            feature = " "
        cell = " %s |" % (feature,)
        print cell,

        if subsector.subsector_col == 9:
            print ""


def cli_nebula(opts):
    """
    Generate a nebula.

    :param opts:
    :return:
    """

    gen = NebulaGenerator()
    print json.dumps(gen.create_at_location(opts.x_coordinate, opts.y_coordinate), indent=4)


def cli_star(opts):
    """
    Generate a star.

    :param opts:
    :return:
    """
    gen = StarGenerator()
    print json.dumps(gen.create_at_location(opts.x_coordinate, opts.y_coordinate), indent=4)


def cli_asteroid(opts):
    """
    Generate an asteroid.

    :param opts:
    :return:
    """
    gen = AsteroidGenerator()
    print json.dumps(gen.create_at_location(opts.x_coordinate, opts.y_coordinate), indent=4)


if __name__ == "__main__":

    opts = options()

    # assume our sector x and y at (0,0)
    dispatch = {
        "sector": cli_sector,
        "star": cli_star,
        "nebula": cli_nebula,
        "asteroid": cli_asteroid
    }

    if opts.action in dispatch:
        dispatch[opts.action](opts)