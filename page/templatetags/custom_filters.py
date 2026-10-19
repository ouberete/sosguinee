from django import template
import os

from django.templatetags.static import static

register = template.Library()


@register.filter
def existing_image_url(image_field, default_path='img/default_placeholder.png'):
    """Return a stored image URL only when the referenced file still exists."""
    if not default_path:
        default_path = 'img/default_placeholder.png'
    if image_field and getattr(image_field, 'name', None):
        storage = getattr(image_field, 'storage', None)
        if storage:
            try:
                if storage.exists(image_field.name):
                    return image_field.url
            except Exception:
                try:
                    return image_field.url
                except Exception:
                    pass
        else:
            try:
                return image_field.url
            except Exception:
                pass
    return static(default_path)


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


@register.filter
def is_pdf_file(value):
    """
    Détermine si un fichier est un document PDF selon son extension.
    """
    if not value:
        return False

    filename = getattr(value, "name", str(value))
    extension = os.path.splitext(filename)[1].lower()
    return extension == ".pdf"


@register.filter
def is_word_file(value):
    """
    Détermine si un fichier est un document Word (.doc, .docx) selon son extension.
    """
    if not value:
        return False

    filename = getattr(value, "name", str(value))
    extension = os.path.splitext(filename)[1].lower()
    return extension in {".doc", ".docx"}


@register.filter
def file_extension(value):
    """
    Renvoie l'extension d'un fichier en majuscule sans le point (ex: PDF, DOCX, PNG).
    """
    if not value:
        return ""
    filename = getattr(value, "name", str(value))
    ext = os.path.splitext(filename)[1].lower()
    return ext[1:].upper() if ext.startswith(".") else ext.upper()


@register.filter
def file_basename(value):
    """
    Renvoie le nom du fichier sans le chemin relatif.
    """
    if not value:
        return ""
    filename = getattr(value, "name", str(value))
    return os.path.basename(filename)
