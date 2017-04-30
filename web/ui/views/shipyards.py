"""
The market place handles goods transactions.
"""
from ui.util import fill_context
from ui.models import Ship, Planet, ShipYard

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction


def yard(request, ship_id, shipyard_id):
    """
    List the contents of the shipyard

    :param request:
    :param ship_id:
    :param planet_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    shipyard = get_object_or_404(ShipYard, pk=shipyard_id)
    planet = shipyard.planet

    # are we actually at this planet?
    if ship.planet != planet:
        return redirect(reverse("ship", args=(ship_id,)))

    # does the user actually own this ship?
    if request.user.profile != ship.owner:
        return redirect(reverse("ships"))

    return render(request, "shipyards/yard.html", context=fill_context({"ship": ship, "planet": planet, "shipyard": shipyard}))

