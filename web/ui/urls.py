"""web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from ui.views import index
from ui.views import planets

urlpatterns = [
    url(r'^$', index.index),

    url(r'^planets/$', planets.list, name="planets"),
    url(r'^planets/create/random/?$', planets.create_random, name="planets-create-random"),
    url(r'^planet/(?P<planet_id>[0-9]+)/?$', planets.detail, name="planet"),
    url(r'^planet/(?P<planet_id>[0-9]+)/remove/?$', planets.remove, name="planet-remove"),
]
