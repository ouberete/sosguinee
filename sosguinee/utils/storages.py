"""
Backends de stockage des médias sur un service objet S3-compatible
(AWS S3 ou OVH Object Storage, selon AWS_S3_ENDPOINT_URL).

Deux stockages distincts :

- ``PublicMediaStorage``  : bucket public (images d'alertes/financements).
  URLs permanentes, sans signature — servies directement par le bucket.
  C'est le stockage PAR DÉFAUT en prod (voir STORAGES dans settings).

- ``PrivateMediaStorage`` : bucket privé (pièces d'identité: id_card,
  birth_piece, photo). ``url()`` ne renvoie JAMAIS d'URL S3 (présignée ou
  non) mais l'URL de la vue Django gardée ``/media/user_images/...`` : le
  contrôle d'accès propriétaire/staff reste le seul point de sortie.

En dev (USE_S3=False), on retombe sur le stockage disque local habituel.
"""
from urllib.parse import quote

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    def __init__(self, **kwargs):
        kwargs.setdefault("bucket_name", settings.AWS_STORAGE_BUCKET_NAME)
        kwargs.setdefault("querystring_auth", False)
        kwargs.setdefault("default_acl", "public-read")
        kwargs.setdefault("file_overwrite", False)
        super().__init__(**kwargs)


class PrivateMediaStorage(S3Boto3Storage):
    def __init__(self, **kwargs):
        kwargs.setdefault("bucket_name", settings.AWS_PRIVATE_STORAGE_BUCKET_NAME)
        kwargs.setdefault("querystring_auth", True)
        kwargs.setdefault("default_acl", "private")
        kwargs.setdefault("file_overwrite", False)
        super().__init__(**kwargs)

    def url(self, name, parameters=None, expire=None, http_method=None):
        # Sécurité: aucune URL S3 directe pour les documents personnels.
        # On renvoie l'URL de la vue Django authentifiée (protected_user_document).
        media_url = settings.MEDIA_URL
        if not media_url.endswith("/"):
            media_url += "/"
        return f"{media_url}{quote(name.lstrip('/'))}"


def select_private_storage():
    """Storage à utiliser pour les champs de documents personnels.

    Callable (et non instance) afin que le choix S3/disque soit résolu au
    démarrage selon USE_S3, et que la migration ne fige pas de bucket.
    """
    if getattr(settings, "USE_S3", False):
        return PrivateMediaStorage()
    return FileSystemStorage()
