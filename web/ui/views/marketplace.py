"""
The market place handles goods transactions.
"""
from ui.util import fill_context
from ui.models import Ship, Planet

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction

def goods(request, ship_id, planet_id):
    """
    List the goods available to a ship at a planet.

    :param request:
    :param ship_id:
    :param planet_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    planet = get_object_or_404(Planet, pk=planet_id)

    # are we actually at this planet?
    if ship.planet != planet:
        return redirect(reverse("ship", args=(ship_id,)))

    # does the user actually own this ship?
    if request.user.profile != ship.owner:
        return redirect(reverse("ships"))

    return render(request, "marketplace/goods.html", context=fill_context({"ship": ship, "planet": planet}))