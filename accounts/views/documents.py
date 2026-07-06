"""
Distribution contrôlée des documents personnels (pièces d'identité, actes
de naissance, photos de profil) stockés sous media/user_images/.

Ces fichiers ne doivent JAMAIS être servis publiquement par le serveur de
fichiers (nginx, whitenoise) : l'URL /media/user_images/<...> est routée
vers cette vue, qui n'autorise que le propriétaire du document ou un membre
du staff. Un 404 (et non 403) est renvoyé dans les autres cas afin de ne
pas révéler l'existence d'un fichier.
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404

from page.models import UserDetails


@login_required
def protected_user_document(request, path):
    relative = f"user_images/{path}"

    # Le fichier doit être rattaché à un profil (empêche au passage toute
    # traversée de répertoire: seuls des chemins enregistrés en base sortent).
    record = (
        UserDetails.objects.filter(
            Q(id_card=relative) | Q(birth_piece=relative) | Q(photo=relative)
        )
        .select_related("user")
        .first()
    )
    if record is None:
        raise Http404

    if record.user_id != request.user.id and not request.user.is_staff:
        raise Http404

    file_path = (Path(settings.MEDIA_ROOT) / relative).resolve()
    media_root = Path(settings.MEDIA_ROOT).resolve()
    if media_root not in file_path.parents or not file_path.is_file():
        raise Http404

    return FileResponse(open(file_path, "rb"))
