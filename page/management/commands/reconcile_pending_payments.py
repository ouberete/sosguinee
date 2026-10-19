import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from page.models import Donation, FundPayment
from page.views import reconcile_payment_with_djomy

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Reconcilie automatiquement les paiements en attente (Donation et FundPayment) "
        "en interrogeant l'API Djomy. Ideal a executer via une tache cron toutes les 15 minutes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=5,
            help="Age minimal en minutes d'un paiement en attente avant verification (defaut: 5 min).",
        )
        parser.add_argument(
            "--max-hours",
            type=int,
            default=72,
            help="Age maximal en heures pour rechercher les paiements en attente (defaut: 72h).",
        )
        parser.add_argument(
            "--model",
            choices=["all", "donation", "fundpayment"],
            default="all",
            help="Type de modele a reconcilier : 'all', 'donation', ou 'fundpayment' (defaut: 'all').",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Nombre maximal de paiements a traiter par modele (defaut: 100).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule la verification sans enregistrer les modifications.",
        )

    def handle(self, *args, **options):
        min_minutes = options["minutes"]
        max_hours = options["max_hours"]
        target_model = options["model"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        now = timezone.now()
        min_created = now - timedelta(hours=max_hours)
        max_created = now - timedelta(minutes=min_minutes)

        if dry_run:
            self.stdout.write(self.style.WARNING("--- MODE DRY-RUN ACTIF (aucune modification enregistree) ---"))

        self.stdout.write(
            f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Lancement de la reconciliation des paiements en attente "
            f"(crees entre {min_created.strftime('%Y-%m-%d %H:%M')} et {max_created.strftime('%Y-%m-%d %H:%M')})..."
        )

        models_to_check = []
        if target_model in ("all", "donation"):
            models_to_check.append((Donation, "Donation"))
        if target_model in ("all", "fundpayment"):
            models_to_check.append((FundPayment, "FundPayment"))

        total_checked = 0
        total_confirmed = 0
        total_failed = 0
        total_pending = 0
        total_unresolved = 0

        for model_cls, model_name in models_to_check:
            qs = model_cls.objects.filter(
                status="en_attente",
                created_at__gte=min_created,
                created_at__lte=max_created,
            ).order_by("created_at")

            if limit > 0:
                qs = qs[:limit]

            count = qs.count()
            self.stdout.write(f"\n{model_name} : {count} paiement(s) en attente a analyser.")

            for payment in qs.iterator():
                total_checked += 1
                ref = getattr(payment, "reference", "") or f"#{payment.pk}"
                amount = getattr(payment, "amount", 0)

                self.stdout.write(
                    f"  - {model_name} {ref} ({amount} GNF, cree le {payment.created_at.strftime('%d/%m %H:%M')}) : ",
                    ending="",
                )

                if dry_run:
                    self.stdout.write(self.style.NOTICE("SIMULATION (Dry-run)"))
                    continue

                try:
                    result = reconcile_payment_with_djomy(payment)
                    status = result.get("status")
                    updated = result.get("updated")

                    if status == "réussi":
                        total_confirmed += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"CONFIRME (credit et compta valides, net={payment.received_amount})")
                        )
                    elif status == "échoué":
                        total_failed += 1
                        self.stdout.write(self.style.ERROR("ECHOUE (marque comme echoue)"))
                    elif status == "en_attente":
                        total_pending += 1
                        self.stdout.write(self.style.WARNING("EN COURS (toujours en attente chez Djomy)"))
                    else:
                        total_unresolved += 1
                        self.stdout.write(self.style.NOTICE(f"NON RESOLU ({result.get('message')})"))
                except Exception as exc:
                    total_unresolved += 1
                    logger.exception("Erreur lors de la reconciliation du paiement %s %s: %s", model_name, ref, exc)
                    self.stdout.write(self.style.ERROR(f"ERREUR : {exc}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            f"Bilan reconciliation : {total_checked} verifie(s) | "
            f"{total_confirmed} confirme(s) | "
            f"{total_failed} echoue(s) | "
            f"{total_pending} toujours en attente | "
            f"{total_unresolved} non resolu(s)."
        )
        self.stdout.write("=" * 60 + "\n")

