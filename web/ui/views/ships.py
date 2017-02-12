"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship, Planet

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse


def list(request):
    """
    The current set of ships.

    :param request:
    :return:
    """
    all_ships = Ship.objects.all()
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
    travel_planets = ship.planets_in_range()
    return render(request, "ships/detail.html", context=fill_context({"ship": ship, "planets": travel_planets}))


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