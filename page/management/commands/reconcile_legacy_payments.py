import logging
from decimal import Decimal

from django.core.management.base import BaseCommand

from page.models import Donation, FundPayment, FundingRequest
from page.views import (
    _finalize_funding_request_status,
    _verify_payment_status_with_djomy,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Reconcilie les anciens paiements reussis dont les frais et le montant net "
        "sont inconnus (NULL suite a la migration 0046)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule la reconciliation sans enregistrer les modifications en base.",
        )
        parser.add_argument(
            "--model",
            choices=["all", "donation", "fundpayment"],
            default="all",
            help="Modele(s) a traiter : 'all', 'donation', ou 'fundpayment'.",
        )
        parser.add_argument(
            "--assume-zero-fees",
            action="store_true",
            help=(
                "Si l'API Djomy ne retourne pas de details comptables, definit "
                "received_amount = amount et fees = 0."
            ),
        )
        parser.add_argument(
            "--recalculate-funding-totals",
            action="store_true",
            help=(
                "Recalcule FundingRequest.amount_received pour chaque collecte "
                "concernee en sommant les montants nets des paiements reussis."
            ),
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Nombre maximal de paiements a traiter par modele (0 = aucun filtre).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        target_model = options["model"]
        assume_zero = options["assume_zero_fees"]
        recalc_totals = options["recalculate_funding_totals"]
        limit = options["limit"]

        if dry_run:
            self.stdout.write(self.style.WARNING("--- MODE DRY-RUN ACTIF (aucune ecriture) ---"))

        models_to_process = []
        if target_model in ("all", "donation"):
            models_to_process.append((Donation, "Donation"))
        if target_model in ("all", "fundpayment"):
            models_to_process.append((FundPayment, "FundPayment"))

        total_checked = 0
        total_reconciled_djomy = 0
        total_reconciled_fallback = 0
        total_unresolved = 0
        affected_funding_ids = set()

        for model_cls, model_name in models_to_process:
            qs = model_cls.objects.filter(
                status="réussi",
                received_amount__isnull=True,
            ).order_by("created_at")

            if limit > 0:
                qs = qs[:limit]

            self.stdout.write(
                f"Traitement de {model_name}: {qs.count()} paiement(s) a reconcilier..."
            )

            for payment in qs.iterator():
                total_checked += 1
                ref = getattr(payment, "reference", "") or f"#{payment.pk}"
                self.stdout.write(f"  Paiement {model_name} {ref} (montant brut: {payment.amount} GNF)...", ending=" ")

                # 1. Tentative d'interrogation de Djomy
                try:
                    _verify_payment_status_with_djomy(payment)
                except Exception as exc:
                    logger.warning("Erreur lors de la verification Djomy pour %s#%s: %s", model_name, payment.pk, exc)

                payment.refresh_from_db()
                if payment.received_amount is not None and payment.fees is not None:
                    total_reconciled_djomy += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"OK (Djomy: net={payment.received_amount}, frais={payment.fees})"
                        )
                    )
                    if hasattr(payment, "funding_request_id") and payment.funding_request_id:
                        affected_funding_ids.add(payment.funding_request_id)
                    continue

                # 2. Fallback --assume-zero-fees si demande
                if assume_zero:
                    if not dry_run:
                        payment.received_amount = payment.amount
                        payment.fees = Decimal("0.00")
                        payment.provider_currency = getattr(payment, "provider_currency", "") or "GNF"
                        payment.save(update_fields=["received_amount", "fees", "provider_currency", "updated_at"])
                    total_reconciled_fallback += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"RECONCILIE FALLBACK (frais=0, net={payment.amount})"
                        )
                    )
                    if hasattr(payment, "funding_request_id") and payment.funding_request_id:
                        affected_funding_ids.add(payment.funding_request_id)
                else:
                    total_unresolved += 1
                    self.stdout.write(
                        self.style.NOTICE(
                            "NON RESOLU (aucune donnee comptable Djomy, specifier --assume-zero-fees pour forcer)"
                        )
                    )

        # 3. Recalcul eventuel de FundingRequest.amount_received
        if recalc_totals and affected_funding_ids:
            self.stdout.write("\nRecalcul des totaux des collectes de financement...")
            for fr_id in sorted(affected_funding_ids):
                try:
                    fr = FundingRequest.objects.get(pk=fr_id)
                    payments = FundPayment.objects.filter(
                        funding_request=fr,
                        status="réussi",
                    )
                    total_amount = sum(
                        (p.amount for p in payments),
                        Decimal("0.00"),
                    )
                    old_amount = fr.amount_received or Decimal("0.00")
                    self.stdout.write(
                        f"  Collecte #{fr.pk} ({fr.title}): ancien total={old_amount} GNF -> nouveau total={total_amount} GNF"
                    )
                    if not dry_run:
                        fr.amount_received = total_amount
                        fr.save(update_fields=["amount_received", "updated_at"])
                        _finalize_funding_request_status(fr)
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"  Erreur collecte #{fr_id}: {exc}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nBilan: {total_checked} verifie(s), "
                f"{total_reconciled_djomy} reconcilie(s) via Djomy, "
                f"{total_reconciled_fallback} reconcilie(s) via fallback 0 frais, "
                f"{total_unresolved} non resolu(s)."
            )
        )
