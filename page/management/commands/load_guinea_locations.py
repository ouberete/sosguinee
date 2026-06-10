from __future__ import annotations

import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from page.models import Commune, Prefecture, Quarter, Region


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_JSON = DATA_DIR / "guinea_locations.json"
DEFAULT_CSV = DATA_DIR / "guinea_locations.csv"

SECTION_ALIASES = {
    "prefectures": ("Prefectures", "Préfectures", "PrÃ©fectures"),
    "communes": ("Communes",),
    "quarters": ("Quartiers", "Districts", "Secteurs", "Sectors"),
}


def _clean(value) -> str:
    return str(value or "").strip()


def _first_section(mapping, section_name):
    for key in SECTION_ALIASES.get(section_name, (section_name,)):
        section = mapping.get(key)
        if isinstance(section, dict):
            return section
    return {}


def _load_json_dataset(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise CommandError("Le fichier JSON doit contenir un objet racine de type dictionnaire.")
    return data


def _load_csv_dataset(path: Path) -> dict:
    dataset: dict = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            region_name = _clean(row.get("region"))
            prefecture_name = _clean(row.get("prefecture"))
            commune_name = _clean(row.get("commune"))
            quarter_name = _clean(row.get("quarter") or row.get("district") or row.get("sector"))

            if not (region_name and prefecture_name and commune_name):
                continue

            dataset.setdefault(region_name, {"Prefectures": {}})
            dataset[region_name]["Prefectures"].setdefault(prefecture_name, {"Communes": {}})
            dataset[region_name]["Prefectures"][prefecture_name]["Communes"].setdefault(commune_name, [])
            if quarter_name:
                dataset[region_name]["Prefectures"][prefecture_name]["Communes"][commune_name].append(quarter_name)
    return dataset


def _load_dataset(path: Path | None = None) -> tuple[dict, str]:
    if path is not None:
        if not path.exists():
            raise CommandError(f"Fichier introuvable: {path}")
        if path.suffix.lower() == ".json":
            return _load_json_dataset(path), str(path)
        if path.suffix.lower() == ".csv":
            return _load_csv_dataset(path), str(path)
        raise CommandError("Format de fichier non supporté. Utilisez un fichier .json ou .csv.")

    if DEFAULT_JSON.exists():
        return _load_json_dataset(DEFAULT_JSON), str(DEFAULT_JSON)
    if DEFAULT_CSV.exists():
        return _load_csv_dataset(DEFAULT_CSV), str(DEFAULT_CSV)
    raise CommandError("Aucune source de données trouvée dans page/data.")


def _iterate_hierarchy(dataset: dict):
    for region_name, region_data in dataset.items():
        if not isinstance(region_data, dict):
            continue
        prefectures = _first_section(region_data, "prefectures")
        yield _clean(region_name), prefectures


def _iter_communes(prefecture_data: dict):
    communes = _first_section(prefecture_data, "communes")
    for commune_name, quarters in communes.items():
        yield _clean(commune_name), quarters if isinstance(quarters, list) else []


class Command(BaseCommand):
    help = (
        "Charge les localités de Guinée (8 régions, 33 préfectures, communes et quartiers/districts) "
        "dans la base. La commande est idempotente et peut repartir de zéro avec --reset."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin vers un fichier JSON hiérarchique ou CSV avec colonnes region,prefecture,commune,quarter.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime d'abord les régions, préfectures, communes et quartiers existants avant de reseeder.",
        )
        parser.add_argument(
            "--purge-inconnue",
            action="store_true",
            help="Supprime les entrées nommées 'Inconnue' si elles ne sont plus référencées.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait chargé sans écrire en base.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        source_path = Path(options["file"]).expanduser() if options.get("file") else None
        dataset, source_label = _load_dataset(source_path)

        if options.get("reset"):
            quarter_count = Quarter.objects.count()
            commune_count = Commune.objects.count()
            prefecture_count = Prefecture.objects.count()
            region_count = Region.objects.count()

            Quarter.objects.all().delete()
            Commune.objects.all().delete()
            Prefecture.objects.all().delete()
            Region.objects.all().delete()

            self.stdout.write(
                self.style.WARNING(
                    f"Réinitialisation effectuée: -{region_count} régions, -{prefecture_count} préfectures, "
                    f"-{commune_count} communes, -{quarter_count} quartiers."
                )
            )

        created_regions = created_prefectures = created_communes = created_quarters = 0

        for region_name, prefectures in _iterate_hierarchy(dataset):
            if not region_name:
                continue
            if options.get("dry_run"):
                created_regions += 1
                for pref_name, pref_data in prefectures.items():
                    if not _clean(pref_name):
                        continue
                    created_prefectures += 1
                    communes = _first_section(pref_data, "communes")
                    for commune_name, quarters in communes.items():
                        if not _clean(commune_name):
                            continue
                        created_communes += 1
                        created_quarters += len(quarters or [])
                continue

            region, created = Region.objects.get_or_create(name=region_name)
            created_regions += int(created)

            for prefecture_name, prefecture_data in prefectures.items():
                prefecture_name = _clean(prefecture_name)
                if not prefecture_name:
                    continue

                prefecture, created = Prefecture.objects.get_or_create(
                    name=prefecture_name,
                    region=region,
                )
                created_prefectures += int(created)

                for commune_name, quarters in _iter_communes(prefecture_data):
                    if not commune_name:
                        continue

                    commune, created = Commune.objects.get_or_create(
                        name=commune_name,
                        prefecture=prefecture,
                    )
                    created_communes += int(created)

                    for quarter_name in quarters or []:
                        quarter_name = _clean(quarter_name)
                        if not quarter_name:
                            continue
                        quarter, created = Quarter.objects.get_or_create(
                            name=quarter_name,
                            commune=commune,
                        )
                        created_quarters += int(created)

        if options.get("dry_run"):
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Source: {source_label} | régions={created_regions}, préfectures={created_prefectures}, "
                    f"communes={created_communes}, quartiers={created_quarters}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Chargement terminé depuis {source_label}: +{created_regions} régions, +{created_prefectures} préfectures, "
                f"+{created_communes} communes, +{created_quarters} quartiers."
            )
        )

        if options.get("purge_inconnue"):
            removed = 0
            for Model in (Quarter, Commune, Prefecture, Region):
                for obj in Model.objects.filter(name__iexact="Inconnue"):
                    has_refs = any(
                        rel.related_model.objects.filter(**{rel.field.name: obj}).exists()
                        for rel in obj._meta.related_objects
                    )
                    if not has_refs:
                        obj.delete()
                        removed += 1
            self.stdout.write(self.style.WARNING(f"Entrées 'Inconnue' supprimées: {removed}"))
