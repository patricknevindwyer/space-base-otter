"""
Control and view planets
"""
from ui.util import fill_context
from ui.models import Ship, Planet

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

def gift_credits(request):
    """
    Gift 100,000 credits to the user.

    :param request:
    :return:
    """
    request.user.profile.add_credits(100000)
    return redirect(reverse("account-profile"))
