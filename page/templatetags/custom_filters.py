from django import template

register = template.Library()

@register.filter
def startswith(value, arg):
    return value.startswith(arg)


@register.filter
def formatFrenchCurrency(value):
    return f"{value:.2f} GNF"