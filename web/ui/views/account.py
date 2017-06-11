"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship, Location

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    """
    User profile.

    :param request:
    :return:
    """
    return render(request, "accounts/profile.html", context=fill_context({}))


def give_credits(request, creds):
    """
    Gift X credits to the user.

    :param request:
    :return:
    """
    request.user.profile.add_credits(int(creds))
    return redirect(reverse("account-profile"))


def take_credits(request, creds):
    """
    This is just a quick and dirty utility for manipulating user credits
    when testing. Not designed to be atomic, or generally used.

    :param request:
    :param creds:
    :return:
    """
    request.user.profile.subtract_credits(int(creds))
    return redirect(reverse("account-profile"))


def seed_ship(request):
    """
    Give this user a ship.

    :param request:
    :return:
    """
    Ship.objects.seed_ship_for_profile(request.user.profile)
    return redirect(reverse("account-profile"))