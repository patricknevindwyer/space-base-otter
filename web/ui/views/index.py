from ui.util import fill_context
from ui.models import Planet, Ship

from django.shortcuts import render



def index(request):
    """
    :param request:
    :return:
    """
    ctx = {
        "planet_count": Planet.objects.count()
    }

    return render(request, "index.html", context=fill_context(ctx))