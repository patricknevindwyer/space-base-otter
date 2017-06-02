from django import template

register = template.Library()


@register.filter
def has_cargo(ship, good):
    """

    :param ship: models::Ship
    :param good: models::Good

    :return:
    """
    return ship.has_in_cargo(good)


@register.filter
def quantity_in_cargo(ship, good):
    """
    How much of a good does a ship have in cargo?

    :param ship:
    :param good:
    :return:
    """
    return ship.quantity_in_cargo(good)


@register.filter
def can_sell_at_profit(ship, good):
    """
    Given a good in at import, is the ships cargo average prices
     lower than the strike import price?

    :param ship:
    :param good:
    :return:
    """
    cargo = ship.get_cargo_from_good(good)

    if cargo is None:
        return False

    return cargo.average_price() < good.price


@register.filter
def can_buy_upgrade(ship, upgrade):
    """
    Can the ship owner afford and fit the given
    upgrade?
    
    :param ship: 
    :param upgrade: 
    :return: 
    """
    return ship.can_install_upgrade(upgrade) and upgrade.cost <= ship.owner.credits


@register.filter
def can_buy_ship(user, ship):
    """
    Determine if a user can buy a ship.

    :param user:
    :param ship:
    :return:
    """
    return user.profile.credits >= ship.value