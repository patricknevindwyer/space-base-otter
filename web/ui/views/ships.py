"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship, Planet

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
    p = Ship.objects.create_random()
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
    planet = ship.planet

    # only owners can get the details on a ship
    if request.user.profile == ship.owner:
        return render(request, "ships/detail.html", context=fill_context({"ship": ship, "planet": planet}))
    else:
        return redirect(reverse("ships"))


@login_required
def travel(request, ship_id):
    """
    Travel options from a planet.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    planet = ship.planet

    # only owners can get the details on a ship
    if request.user.profile == ship.owner:

        if planet.shipyards.count() == 0:
            planet.add_shipyard()

        return render(request, "ships/travel.html", context=fill_context({"ship": ship, "planet": planet}))
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

    # assign ownership
    ship.owner = user.profile
    ship.save()

    messages.info(request, "Congratulations, you bought a ship!")

    # jump to the ship details
    return redirect(reverse("ship", args=(ship_id,)))


@transaction.atomic
@login_required
def travel_to_planet(request, ship_id, planet_id):
    """
    Make a ship travel to a new planet.

    :param request:
    :param ship_id:
    :param planet_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)
    planet = get_object_or_404(Planet, pk=planet_id)

    distance = ship.distance_to(planet)
    ship.travel_to(planet)
    ship.burn_fuel_for_distance(distance)

    messages.info(request, "Welcome to %s" % (planet.name,))
    return redirect(reverse("ship-travel", args=(ship_id,)))


@transaction.atomic
@login_required
def travel_to_home_planet(request, ship_id):
    """
    Traveling to your home planet burns all of your fuel, and costs $ == distance. If
    the player doesn't have enough money, it drops to 0.

    :param request:
    :param ship_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)

    home_distance = ship.distance_to(ship.home_planet)

    # travel
    ship.travel_to(ship.home_planet)

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