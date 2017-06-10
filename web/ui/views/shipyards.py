"""
The market place handles goods transactions.
"""
from ui.util import fill_context
from ui.models import Ship, Location, ShipYard, ShipUpgrade

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

    print "There are %d ships at the yard" % (shipyard.ships.count(),)
    return render(request, "shipyards/yard.html", context=fill_context({"ship": ship, "planet": planet, "shipyard": shipyard, "upgrade_blurb": ShipUpgrade.objects.upgrade_quality_blurb()}))


def buy_upgrade(request, ship_id, shipyard_id, shipupgrade_id):
    """
    Try and buy and install an upgrade for a ship.
    
    :param request: 
    :param ship_id: 
    :param shipyard_id: 
    :param upgrade_id: 
    :return: 
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    shipyard = get_object_or_404(ShipYard, pk=shipyard_id)
    upgrade = get_object_or_404(ShipUpgrade, pk=shipupgrade_id)
    planet = shipyard.planet

    # are we actually at the planet for this shipyard?
    if ship.planet != planet:
        messages.error(request, "Your ship isn't orbiting near that ShipYard")
        return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))

    # is this the user's ship?
    if request.user.profile != ship.owner:
        messages.error(request, "That's not your ship")
        return redirect(reverse("ships"))

    # do we have enough money?
    if upgrade.cost > request.user.profile.credits:
        messages.error(request, "You can't afford that")
        return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))

    # let's check our capacity
    if upgrade.capacity > ship.upgrade_capacity_free():
        messages.error(request, "You don't have enough upgrade capacity for that")
        return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))

    # can we install it?
    if not ship.can_install_upgrade(upgrade):
        messages.error(request, "You can't install that upgrade")
        return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))

    # buy and install!
    ship.buy_upgrade(upgrade)

    # don't forget to spend money
    request.user.profile.subtract_credits(upgrade.cost)

    messages.success(request, "%s bought and installed!" % (upgrade.name, ))
    # back to the shipyard with you
    return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))


def seed_upgrades(request, ship_id, shipyard_id):
    """
    Seed a shipyard with goods.
    
    :param request: 
    :param ship_id: 
    :param shipyard_id: 
    :return: 
    """

    ship = get_object_or_404(Ship, pk=ship_id)
    shipyard = get_object_or_404(ShipYard, pk=shipyard_id)

    shipyard.seed_upgrades()

    return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))


def seed_ships(request, ship_id, shipyard_id):
    """
    Seed a ship yard with ships.
    
    :param request: 
    :param ship_id: 
    :param shipyard_id: 
    :return: 
    """
    shipyard = get_object_or_404(ShipYard, pk=shipyard_id)

    shipyard.seed_ships(3)

    return redirect(reverse("shipyard", args=(ship_id, shipyard_id)))
