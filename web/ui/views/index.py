from ui.util import fill_context

from django.shortcuts import render

def index(request):
    """
    :param request:
    :return:
    """

    return render(request, "index.html", context=fill_context({}))