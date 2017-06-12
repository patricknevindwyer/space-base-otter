"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Location

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def list(request):
    """
    The current set of planets.

    :param request:
    :return:
    """
    all_planets = Location.objects.all()

    # build pagination
    planet_pager = Paginator(all_planets, 5)
    page = request.GET.get("page")

    try:
        planets = planet_pager.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        planets = planet_pager.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        planets = planet_pager.page(planet_pager.num_pages)

    return render(request, "locations/list.html", context=fill_context({"locations": planets}))


def destroy_all(request):
    """

    :param request:
    :return:
    """
    Location.objects.all().delete()
    return redirect(reverse("planets"))


def create_random(request):
    """

    :param request:
    :return:
    """
    p = Location.objects.create_random()
    return redirect(reverse("planets"))


def create_multiple(request, quantity):
    """

    :param request:
    :return:
    """
    for i in range(int(quantity)):
        p = Location.objects.create_random()
    return redirect(reverse("planets"))


def remove(request, planet_id):
    """
    Remove a planet.

    :param request:
    :param planet_id:
    :return:
    """
    planet = get_object_or_404(Location, pk=planet_id)
    planet.delete()
    return redirect(reverse("planets"))


def destroy_unoccupied(request):
    """
    Delete any planets not currently hosting a player.
    
    :param request: 
    :return: 
    """
    Location.objects.delete_unoccupied()
    return redirect(reverse("planets"))


def detail(request, planet_id):
    """
    Detail of a planet.

    :param request:
    :param planet_id:
    :return:
    """
    planet = get_object_or_404(Location, pk=planet_id)

    return render(request, "locations/detail.html", context=fill_context({"location": planet}))