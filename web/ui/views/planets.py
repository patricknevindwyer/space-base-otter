"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Planet

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse


def list(request):
    """
    The current set of planets.

    :param request:
    :return:
    """
    all_planets = Planet.objects.all()
    return render(request, "planets/list.html", context=fill_context({"planets": all_planets}))


def create_random(request):
    """

    :param request:
    :return:
    """
    p = Planet.objects.create_random()
    return redirect(reverse("planets"))


def remove(request, planet_id):
    """
    Remove a planet.

    :param request:
    :param planet_id:
    :return:
    """
    planet = get_object_or_404(Planet, pk=planet_id)
    planet.delete()
    return redirect(reverse("planets"))


def detail(request, planet_id):
    """
    Detail of a planet.

    :param request:
    :param planet_id:
    :return:
    """
    planet = get_object_or_404(Planet, pk=planet_id)
    return render(request, "planets/detail.html", context=fill_context({"planet": planet}))