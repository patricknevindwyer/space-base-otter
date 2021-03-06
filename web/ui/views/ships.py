"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship, Location

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction

from django.contrib.auth.decorators import login_required

@login_required
def list(request):
    """
    The current set of ships.

    :param request:
    :return:
    """
    all_ships = Ship.objects.order_by("value").all()
    return render(request, "ships/list.html", context=fill_context({"ships": all_ships}))


@login_required
def create_random(request):
    """

    :param request:
    :return:
    """
    print "! DEPRECATED - Ships.py::create_random is a deprecated methods"
    return redirect(reverse("ships"))


@login_required
def remove(request, ship_id):
    """
    Remove a ship.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    ship.delete()
    return redirect(reverse("ships"))


@login_required
def detail(request, ship_id):
    """
    Detail of a ships.

    :param request:
    :param planet_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    location = ship.location

    # only owners can get the details on a ship
    if request.user.profile == ship.owner:
        return render(request, "ships/detail.html", context=fill_context({"ship": ship, "location": location}))
    else:
        return redirect(reverse("ships"))


@login_required
def travel(request, ship_id):
    """
    Travel options from a location.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    location = ship.location

    # only owners can get the details on a ship
    if request.user.profile == ship.owner:

        if location.shipyards.count() == 0:
            location.add_shipyard()

        return render(request, "ships/travel.html", context=fill_context({"ship": ship, "location": location}))
    else:
        return redirect(reverse("ships"))


@transaction.atomic
@login_required
def buy(request, ship_id):
    """
    Try and buy this ship.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    user = request.user

    # get some pre-reqs out of the way

    # does this ship already have an owner?
    if ship.owner is not None:
        messages.error(request, "That ship is already owned by another player")
        return redirect(reverse("ships"))

    # is this ship too expensive
    if ship.value > user.profile.credits:
        messages.error(request, "That ship is too expensive for you to purchase")
        return redirect(reverse("ships"))

    # looks like a good transaction

    # exchange money
    user.profile.credits = user.profile.credits - ship.value
    user.profile.save()

    # track our yard - we may need to refresh ships
    yard = ship.shipyard

    # assign ownership
    ship.owner = user.profile
    ship.shipyard = None
    ship.save()

    if yard.ships.count() == 0:
        yard.seed_ships(3)

    messages.info(request, "Congratulations, you bought a ship!")

    # jump to the ship details
    return redirect(reverse("ship", args=(ship_id,)))


@transaction.atomic
@login_required
def travel_to_location(request, ship_id, location_id):
    """
    Make a ship travel to a new location.

    :param request:
    :param ship_id:
    :param location_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    location = get_object_or_404(Location, pk=location_id)

    distance = ship.distance_to(location)
    ship.travel_to(location)
    ship.burn_fuel_for_distance(distance)

    messages.info(request, "Welcome to %s" % (location.name,))
    return redirect(reverse("ship-travel", args=(ship_id,)))


@transaction.atomic
@login_required
def travel_to_home_location(request, ship_id):
    """
    Traveling to your home planet burns all of your fuel, and costs $ == distance. If
    the player doesn't have enough money, it drops to 0.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)

    home_distance = ship.distance_to(ship.home_location)

    # travel
    ship.travel_to(ship.home_location)

    # fuel
    ship.fuel_level = 0.0
    ship.save()

    # money
    request.user.profile.subtract_credits(home_distance)

    return redirect(reverse("ship-travel", args=(ship_id,)))


@login_required
def refuel(request, ship_id):
    """
    Refuel as much of the ship as possible.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)

    if ship.can_fully_refuel():
        request.user.profile.subtract_credits(ship.refuel_cost())
        ship.refuel()
    else:
        creds = request.user.profile.credits
        request.user.profile.subtract_credits(creds)
        ship.partially_refuel(creds)
    return redirect(reverse("ship-travel", args=(ship_id,)))