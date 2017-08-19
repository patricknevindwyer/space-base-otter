from ui.util import fill_context
from ui.models import Location, Ship

from django.db.models import Count
from django.shortcuts import render



def index(request):
    """
    :param request:
    :return:
    """

    # let's get a count of our different location types
    location_counts = Location.objects.values("location_type").annotate(count=Count('id'))
    ctx = {
        "location_counts": location_counts
    }

    return render(request, "index.html", context=fill_context(ctx))