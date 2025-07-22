from django import template

register = template.Library()

@register.filter
def startswith(value, arg):
    return value.startswith(arg)


@register.filter
def formatFrenchCurrency(value):
    return f"{value:.2f} GNF"

@register.filter
def format_fr(value):
    """
    Affiche un entier en format français avec des espaces comme séparateurs.
    Ex: 1000000 -> '1 000 000'
    """
    try:
        return f"{int(value):,}".replace(",", " ").replace("\xa0", " ")
    except (ValueError, TypeError):
        return value