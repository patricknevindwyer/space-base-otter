

# Creating Sectors

The `smooth_space_generator` can be used to build the source objects for
a new sector, while the `realizer` can convert that source object list
into real database objects.


Creating a new Sector (at sector location _(0, 0)_ ):

```shell
docker-compose run web python manage.py shell
>>> from ui.generation.smooth_space_generator import SectorGenerator
>>> from ui.generation.realizer import SectorRealizer
>>> generator = SectorGenerator()
>>> generator.sector_x = 0
>>> generator.sector_y = 0
>>> (features, sector_map) = generator.generate()
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
>>> realizer = SectorRealizer()
>>> locations = realizer.realize(features)
3030 locations generated
```