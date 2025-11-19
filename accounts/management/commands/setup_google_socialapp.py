from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from pathlib import Path
import json
import os


class Command(BaseCommand):
    help = "Crée/Met à jour l'app Google (allauth SocialApp) à partir d'un client_secret JSON ou des variables d'environnement."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Chemin vers client_secret_*.json Google')
        parser.add_argument('--site-id', type=int, default=1, help='ID du Site (default: 1)')

    def handle(self, *args, **opts):
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        secret = os.getenv('GOOGLE_CLIENT_SECRET')

        path = opts.get('file')
        if path:
            p = Path(path)
            if not p.exists():
                raise CommandError(f"Fichier introuvable: {path}")
            data = json.loads(p.read_text(encoding='utf-8'))
            try:
                web = data.get('web') or {}
                client_id = web.get('client_id') or client_id
                secret = web.get('client_secret') or secret
            except Exception:
                pass

        if not client_id or not secret:
            raise CommandError('Client ID / Secret introuvables. Fournissez --file ou définissez GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET')

        site = Site.objects.get(pk=opts['site_id'])
        # Ensure single SocialApp for 'google' on this site
        apps_qs = SocialApp.objects.filter(provider='google').order_by('id')
        if apps_qs.exists():
            app = apps_qs.first()
            # Delete all others
            for other in apps_qs[1:]:
                other.delete()
            created = False
        else:
            app = SocialApp(provider='google', name='Google')
            created = True

        app.client_id = client_id
        app.secret = secret
        app.name = 'Google'
        app.save()
        app.sites.set([site])
        self.stdout.write(self.style.SUCCESS(f"SocialApp Google {'créée' if created else 'mise à jour'} (site={site.domain})"))
