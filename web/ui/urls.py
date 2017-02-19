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
from django.conf.urls import url, include
from ui.views import index
from ui.views import planets, ships, account

urlpatterns = [
    url(r'^$', index.index),

    url('^', include('django.contrib.auth.urls')),

    url(r'^accounts/profile/?$', account.profile, name="account-profile"),
    url(r'^accounts/profile/gift/?$', account.gift_credits, name="account-gift"),

    url(r'^planets/$', planets.list, name="planets"),
    url(r'^planets/create/random/?$', planets.create_random, name="planets-create-random"),
    url(r'^planets/create/(?P<quantity>[0-9]+)/?$', planets.create_multiple, name="planets-create-multiple"),
    url(r'^planet/(?P<planet_id>[0-9]+)/?$', planets.detail, name="planet"),
    url(r'^planet/(?P<planet_id>[0-9]+)/remove/?$', planets.remove, name="planet-remove"),
    url(r'^planet/destroy/all/?$', planets.destroy_all, name="planets-destroy-all"),

    url(r'^ships/$', ships.list, name="ships"),
    url(r'^ships/create/random/?$', ships.create_random, name="ships-create-random"),
    url(r'^ship/(?P<ship_id>[0-9]+)/?$', ships.detail, name="ship"),
    url(r'^ship/(?P<ship_id>[0-9]+)/buy/?$', ships.buy, name="ship-buy"),
    url(r'^ship/(?P<ship_id>[0-9]+)/remove/?$', ships.remove, name="ship-remove"),
    url(r'^ship/(?P<ship_id>[0-9]+)/travel_to/planet/(?P<planet_id>[0-9]+)/?$', ships.travel_to_planet, name="ship-travel-to-planet"),

]
