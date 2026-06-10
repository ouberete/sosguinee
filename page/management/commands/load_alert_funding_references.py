from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import ProtectedError

from page.models import FundingRequestStatus, FundingType, LossAlertStatus, LossAlertType


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_FILE = DATA_DIR / "default_alert_funding_references.json"

MODEL_MAP = {
    "loss_alert_types": LossAlertType,
    "loss_alert_statuses": LossAlertStatus,
    "funding_types": FundingType,
    "funding_request_statuses": FundingRequestStatus,
}


def _clean(value) -> str:
    return str(value or "").strip()


def _load_dataset(path: Path) -> dict:
    if not path.exists():
        raise CommandError(f"Fichier introuvable: {path}")
    if path.suffix.lower() != ".json":
        raise CommandError("Le format de fichier doit être JSON (.json).")

    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise CommandError("Le fichier JSON doit contenir un objet racine de type dictionnaire.")
    return data


def _validate_entries(section_name: str, entries) -> list[dict]:
    if not isinstance(entries, list):
        raise CommandError(f"La section '{section_name}' doit être une liste d'objets.")

    normalized = []
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise CommandError(f"Entrée invalide dans '{section_name}' à l'index {idx}: objet attendu.")
        name = _clean(entry.get("name"))
        description = _clean(entry.get("description"))
        if not name:
            raise CommandError(f"Entrée invalide dans '{section_name}' à l'index {idx}: 'name' est requis.")
        normalized.append({"name": name, "description": description})
    return normalized


class Command(BaseCommand):
    help = (
        "Charge automatiquement les types/statuts d'alertes et de demandes de financement "
        "de manière idempotente."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(DEFAULT_FILE),
            help="Chemin vers le fichier JSON des référentiels.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime d'abord les référentiels existants (si non référencés) avant rechargement.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche les actions sans écrire en base.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        source_path = Path(options["file"]).expanduser()
        dataset = _load_dataset(source_path)
        dry_run = bool(options.get("dry_run"))
        reset = bool(options.get("reset"))

        validated_sections: dict[str, list[dict]] = {}
        for section_name in MODEL_MAP:
            validated_sections[section_name] = _validate_entries(section_name, dataset.get(section_name, []))

        if reset:
            if dry_run:
                self.stdout.write(self.style.WARNING("[dry-run] --reset demandé: suppression simulée."))
            else:
                for section_name, model in MODEL_MAP.items():
                    try:
                        deleted_count, _ = model.all_objects.all().delete()
                        self.stdout.write(
                            self.style.WARNING(f"Réinitialisation {section_name}: {deleted_count} enregistrements supprimés.")
                        )
                    except ProtectedError as exc:
                        raise CommandError(
                            f"Impossible de supprimer '{section_name}' car des enregistrements sont référencés: {exc}"
                        ) from exc

        summary = {
            "created": 0,
            "updated": 0,
            "reactivated": 0,
            "unchanged": 0,
        }

        for section_name, model in MODEL_MAP.items():
            for entry in validated_sections[section_name]:
                name = entry["name"]
                description = entry["description"]

                existing = model.all_objects.filter(name__iexact=name).first()
                if existing is None:
                    if dry_run:
                        summary["created"] += 1
                        continue
                    model.objects.create(name=name, description=description)
                    summary["created"] += 1
                    continue

                changed = False
                if existing.name != name:
                    existing.name = name
                    changed = True
                if existing.description != description:
                    existing.description = description
                    changed = True
                if getattr(existing, "isDeleted", False):
                    existing.isDeleted = False
                    changed = True
                    summary["reactivated"] += 1

                if changed:
                    if not dry_run:
                        existing.save(update_fields=["name", "description", "isDeleted", "updated_at"])
                    summary["updated"] += 1
                else:
                    summary["unchanged"] += 1

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Chargement terminé depuis {source_path}: "
                f"+{summary['created']} créés, {summary['updated']} mis à jour, "
                f"{summary['reactivated']} réactivés, {summary['unchanged']} inchangés."
            )
        )
