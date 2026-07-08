"""
Distribution contrôlée des documents personnels (pièces d'identité, actes
de naissance, photos de profil) stockés sous user_images/.

Ces fichiers ne doivent JAMAIS être servis publiquement par le serveur de
fichiers (nginx, whitenoise) ni par une URL S3 (présignée ou non) : l'URL
/media/user_images/<...> est routée vers cette vue, qui n'autorise que le
propriétaire du document ou un membre du staff. Un 404 (et non 403) est
renvoyé dans les autres cas afin de ne pas révéler l'existence d'un fichier.

Le fichier est streamé depuis le backend de stockage (disque local en dev,
bucket privé S3/Object Storage en prod) : il ne transite jamais par une URL
publique.
"""
from pathlib import PurePosixPath

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404

from page.models import UserDetails

# Champs de UserDetails susceptibles de contenir un document personnel.
_DOCUMENT_FIELDS = ("id_card", "birth_piece", "photo")


@login_required
def protected_user_document(request, path):
    relative = f"user_images/{path}"

    # Le fichier doit être rattaché à un profil. Comme on ne sert que des
    # chemins enregistrés en base, toute traversée de répertoire est exclue.
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

    # Retrouve le FieldFile exact qui correspond au chemin demandé.
    field_file = None
    for field_name in _DOCUMENT_FIELDS:
        candidate = getattr(record, field_name, None)
        if candidate and candidate.name == relative:
            field_file = candidate
            break
    if field_file is None:
        raise Http404

    try:
        handle = field_file.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404

    return FileResponse(handle, filename=PurePosixPath(relative).name)
