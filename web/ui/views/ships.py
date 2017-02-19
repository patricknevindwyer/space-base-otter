"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship, Planet

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction


def list(request):
    """
    The current set of ships.

    :param request:
    :return:
    """
    all_ships = Ship.objects.order_by("value").all()
    return render(request, "ships/list.html", context=fill_context({"ships": all_ships}))


def create_random(request):
    """

    :param request:
    :return:
    """
    p = Ship.objects.create_random()
    return redirect(reverse("ships"))


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


def detail(request, ship_id):
    """
    Detail of a ships.

    :param request:
    :param planet_id:
    :return:
    """
    ship = get_object_or_404(Ship, pk=ship_id)

    # only owners can get the details on a ship
    if request.user.profile == ship.owner:
        return render(request, "ships/detail.html", context=fill_context({"ship": ship}))
    else:
        return redirect(reverse("ships"))


@transaction.atomic
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

    # jump to the ship details
    return redirect(reverse("ship", args=(ship_id,)))



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

    ship.travel_to(planet)
    return redirect(reverse("ship", args=(ship_id,)))