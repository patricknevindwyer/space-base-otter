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
