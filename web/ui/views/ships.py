"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship

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
    return render(request, "ships/detail.html", context=fill_context({"ship": ship}))