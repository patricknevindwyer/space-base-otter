"""
The market place handles goods transactions.
"""
from ui.util import fill_context
from ui.models import Ship, Location, Good

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction

def goods(request, ship_id, location_id):
    """
    List the goods available to a ship at a location.

    :param request:
    :param ship_id:
    :param location_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    location = get_object_or_404(Location, pk=location_id)

    # are we actually at this location?
    if ship.location != location:
        return redirect(reverse("ship", args=(ship_id,)))

    # does the user actually own this ship?
    if request.user.profile != ship.owner:
        return redirect(reverse("ships"))

    return render(request, "marketplace/goods.html", context=fill_context({"ship": ship, "location": location}))


@transaction.atomic
def import_good(request, ship_id, location_id, good_id, quantity):
    """
    Try and facilitate a location purchasing good from a ship.

    :param request:
    :param ship_id:
    :param location_id:
    :param good_id:
    :param quantity:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    location = get_object_or_404(Location, pk=location_id)
    good = get_object_or_404(Good, pk=good_id)
    quantity = int(quantity)
    price = good.price * quantity

    # are we actually at this location?
    if ship.location != location:
        messages.error(request, "Your ship isn't orbiting that location")
        return redirect(reverse("ship", args=(ship_id,)))

    # does the user actually own this ship?
    if request.user.profile != ship.owner:
        messages.error(request, "That's not your ship")
        return redirect(reverse("ships"))

    # is this good an import for this location?
    if not good.is_import:
        messages.error(request, "That good isn't an export for that location")
        return redirect(reverse("marketplace", args=(ship_id, location_id)))

    # does the user have any of these?
    if not ship.has_in_cargo(good):
        messages.error(request, "You don't have any %s to sell" % (good.name,))
        return redirect(reverse("marketplace", args=(ship_id, location_id)))

    # do we have this many to sell?
    if quantity > ship.quantity_in_cargo(good):
        messages.error(request, "You don't have %d %s to sell" % (quantity, good.name,))
    # let's sell something!
    ship.sell_cargo(good, quantity)

    # don't forget to give the user money!
    request.user.profile.add_credits(price)

    # neat! back to the market place with you
    return redirect(reverse("marketplace", args=(ship_id, location_id)))


@transaction.atomic
def export_good(request, ship_id, location_id, good_id, quantity):
    """
    Try and facilitate a ship purchasing goods from a location.

    :param request:
    :param ship_id:
    :param location_id:
    :param good_id:
    :param quantity:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    location = get_object_or_404(Location, pk=location_id)
    good = get_object_or_404(Good, pk=good_id)
    quantity = int(quantity)
    cost = good.price * quantity

    # a few tests first.

    # are we actually at this location?
    if ship.location != location:
        messages.error(request, "Your ship isn't orbiting that location")
        return redirect(reverse("ship", args=(ship_id,)))

    # does the user actually own this ship?
    if request.user.profile != ship.owner:
        messages.error(request, "That's not your ship")
        return redirect(reverse("ships"))

    # is this good an export for this location?
    if not good.is_export:
        messages.error(request, "That good isn't an export for that location")
        return redirect(reverse("marketplace", args=(ship_id, location_id)))

    # does the user have room for that quantity
    if quantity > ship.cargo_free():
        messages.error(request, "You don't have room for that much cargo")
        return redirect(reverse("marketplace", args=(ship_id, location_id)))

    # can we afford this?
    if cost > request.user.profile.credits:
        messages.error(request, "You can't afford that")
        return redirect(reverse("marketplace", args=(ship_id, location_id)))

    # let's buy something!
    ship.buy_cargo(good, quantity)

    # don't forget to spend money
    request.user.profile.subtract_credits(cost)

    # neat! back to the market place with you
    return redirect(reverse("marketplace", args=(ship_id, location_id)))