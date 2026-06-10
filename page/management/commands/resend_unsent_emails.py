from django.core.management.base import BaseCommand

from page.models import EmailContent
from sosguinee.utils.email_retry import parse_recipients, resend_email_content


class Command(BaseCommand):
    help = "Renvoie les emails EmailContent marques comme non envoyes."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50, help="Nombre maximum d'emails a traiter.")
        parser.add_argument("--dry-run", action="store_true", help="Affiche les emails sans les envoyer.")

    def handle(self, *args, **options):
        limit = options["limit"]
        dry_run = options["dry_run"]
        queryset = EmailContent.all_objects.filter(is_sent=False).order_by("created_at")[:limit]

        sent = 0
        failed = 0
        skipped = 0

        for email_content in queryset:
            recipients = parse_recipients(email_content.receiver_email)
            if not recipients:
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(f"SKIP #{email_content.pk}: aucun destinataire")
                )
                continue

            if dry_run:
                self.stdout.write(f"DRY RUN #{email_content.pk}: {email_content.subjet} -> {', '.join(recipients)}")
                continue

            try:
                sent += resend_email_content(email_content)
                self.stdout.write(self.style.SUCCESS(f"SENT #{email_content.pk}: {email_content.subjet}"))
            except Exception as exc:
                failed += 1
                self.stdout.write(self.style.ERROR(f"FAIL #{email_content.pk}: {exc}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Termine: {sent} envoye(s), {failed} echec(s), {skipped} ignore(s)."
            )
        )
