from django.contrib import admin

from ui.models import Ship, ShipUpgrade

from ui.models import Planet

# Register your models here.

admin.site.register(Ship)
admin.site.register(ShipUpgrade)
admin.site.register(Planet)
