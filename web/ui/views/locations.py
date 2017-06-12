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
    The current set of locations.

    :param request:
    :return:
    """
    all_locations = Location.objects.all()

    # build pagination
    location_pager = Paginator(all_locations, 5)
    page = request.GET.get("page")

    try:
        locations = location_pager.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        locations = location_pager.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        locations = location_pager.page(location_pager.num_pages)

    return render(request, "locations/list.html", context=fill_context({"locations": locations}))


def destroy_all(request):
    """

    :param request:
    :return:
    """
    Location.objects.all().delete()
    return redirect(reverse("locations"))


def create_random(request):
    """

    :param request:
    :return:
    """
    p = Location.objects.create_random()
    return redirect(reverse("locations"))


def create_multiple(request, quantity):
    """

    :param request:
    :return:
    """
    for i in range(int(quantity)):
        p = Location.objects.create_random()
    return redirect(reverse("locations"))


def remove(request, location_id):
    """
    Remove a location.

    :param request:
    :param location_id:
    :return:
    """
    location = get_object_or_404(Location, pk=location_id)
    location.delete()
    return redirect(reverse("locations"))


def destroy_unoccupied(request):
    """
    Delete any locations not currently hosting a player.
    
    :param request: 
    :return: 
    """
    Location.objects.delete_unoccupied()
    return redirect(reverse("locations"))


def detail(request, location_id):
    """
    Detail of a location.

    :param request:
    :param location_id:
    :return:
    """
    location = get_object_or_404(Location, pk=location_id)

    return render(request, "locations/detail.html", context=fill_context({"location": location}))