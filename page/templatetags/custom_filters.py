from django import template
import os

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


@register.filter
def chip_class(value):
    """Return Materialize color classes for a status chip based on text.
    Examples:
      - "En cours" -> orange
      - "Clos"/"Fermé" -> grey
      - "Trouvé" -> teal
      - "En attente"/"Pending" -> orange
      - "Réussi"/"Success" -> green
      - "Échoué"/"Failed" -> red
    """
    if value is None:
        return "blue white-text"
    s = str(value).strip().lower()
    def contains(*keys):
        return any(k in s for k in keys)
    if contains('réussi', 'reussi', 'success'):
        return 'green white-text'
    if contains('blocked', 'bloqu'):
        return 'red white-text'
    if contains('inactive', 'inactif'):
        return 'grey white-text'
    if contains('attente', 'pending'):
        return 'orange white-text'
    if contains('échou', 'echou', 'failed', 'echec'):
        return 'red white-text'
    if contains('en cours', 'cours'):
        return 'orange white-text'
    if contains('clos', 'fermé', 'ferme'):
        return 'grey white-text'
    if contains('trouv'):
        return 'teal white-text'
    return 'blue white-text'


@register.filter
def is_image_file(value):
    """
    Détermine si un fichier est une image selon son extension.
    """
    if not value:
        return False

    filename = getattr(value, "name", str(value))
    extension = os.path.splitext(filename)[1].lower()
    return extension in {".jpg", ".jpeg", ".png", ".webp", ".avif"}
