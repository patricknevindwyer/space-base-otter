"""
Use a sector feature structure to realize actual database objects to
represent the sector.

# Sector Feature Structure

Using a sector generated with `smooth_space_generator`, which looks like:

+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   | N | S | S | S |
+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   | N | S | S | S |
+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   | N | S | S |
+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   | N | N | N |
+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+
|   |   |   |   |   |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+
|   | N | N | N | N |   |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+
| N | N | S | S | N | N |   |   |   |   |
+---+---+---+---+---+---+---+---+---+---+
| S | S | S | S | S | N | N |   | N | N |
+---+---+---+---+---+---+---+---+---+---+
| A | A | A | A | S | S | N | N | S | S |
+---+---+---+---+---+---+---+---+---+---+

we get a 36,755 line JSON structure (pretty printed) that describes all of the
locations within the sector. Each location can be one of:

 - Nebula
 - Asteroid
 - Star
 - Planet
 - Moon

At the top level of the structure there can be only *nebula*, *star*, or
*asteroid* locations. A *star* can have zero or more *planet* locations,
and a *planet* can have zero or more *moon* locations.

All locations in the child stack of a Star will share the same `location_hash`,
and will need to be recursively created so that children are created with a
pointer to their parent location.

A location object looks like:

        {
            "location_hash": "7cd02da13df60c32820fbeb05463a2fd1cb356b2a89491a23099fc258a3004d5",
            "location_meta": {},
            "name": "NGC 5213",
            "fuel_markup": 1.0,
            "y_coordinate": 50,
            "type": "nebula",
            "image_name": "Nebula2.png",
            "x_coordinate": 650.0,
            "children": [...]
        }
"""

from ui.models import Location

class SectorRealizer(object):
    """
    Create a all of the location objects from a newly generated
    sector.
    """

    def __init__(self):
        pass

    def realize(self, sector):
        """
        Realize all of the locations in a sector JSON structure
        into real DB objects. Return the list of created objects.

        :param sector:
        :return:
        """

        locations = []

        for location_json in sector:
            location = self._realize_location(location_json)
            locations += location

        print "%d locations generated" % (len(locations))

        return locations

    def _realize_location(self, location_json, parent=None):
        """
        Given a location, generate the object for this location, as well
        as any children objects. Return the overall list of objects
        created.

        :param location:
        :return:
        """
        locations = []

        # create this object
        location = Location.objects.create(
            name=location_json["name"],

            # location in space
            x_coordinate=location_json["x_coordinate"],
            y_coordinate=location_json["y_coordinate"],

            # UI imagery
            image_name=location_json["image_name"],

            # different locations have different markup on refueling
            fuel_markup=location_json["fuel_markup"],

            # planet/star/asteroid/moon/nebula
            location_type=location_json["type"],

            # resources/etc
            location_meta=location_json["location_meta"],

            # do I have a parent location?
            parent=parent,

            # shared location hash
            location_hash=location_json["location_hash"]
        )
        location.save()

        locations.append(location)

        # create all of the child objects
        if "children" in location_json:
            for child_location_json in location_json["children"]:
                child_location = self._realize_location(child_location_json, parent=location)
                locations += child_location

        return locations

