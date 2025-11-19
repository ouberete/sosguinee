from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from page.models import Region, Prefecture, Commune, Quarter
from pathlib import Path
import json
import csv


DEFAULT_DATA = {
    "Conakry": {
        "Préfectures": {
            "Conakry": {
                "Communes": {
                    "Kaloum": ["Tombo", "Almamya"],
                    "Dixinn": ["Taouyah", "Bellevue"],
                    "Ratoma": ["Kipé", "Nongo", "Kaporo"],
                    "Matam": ["Bonfi", "Madina"],
                    "Matoto": ["Yimbaya", "Gbessia"],
                }
            }
        }
    },
    "Boké": {
        "Préfectures": {
            "Boké": {"Communes": {"Boké Centre": ["Tanènè"]}},
            "Boffa": {"Communes": {"Boffa Centre": ["Koba"]}},
            "Fria": {"Communes": {"Fria Centre": ["Banguigny"]}},
            "Koundara": {"Communes": {"Koundara Centre": ["Sambailo"]}},
            "Gaoual": {"Communes": {"Gaoual Centre": ["Koumbia"]}},
        }
    },
    "Kindia": {
        "Préfectures": {
            "Kindia": {"Communes": {"Kindia Centre": ["Sambaya"]}},
            "Forécariah": {"Communes": {"Forécariah Centre": ["Farmoriah"]}},
            "Dubréka": {"Communes": {"Dubréka Centre": ["Khorira"]}},
            "Télimélé": {"Communes": {"Télimélé Centre": ["Sangaréyah"]}},
            "Coyah": {"Communes": {"Coyah Centre": ["Manéah"]}},
        }
    },
}


class Command(BaseCommand):
    help = "Charge un jeu de données de lieux pour la Guinée (Régions, Préfectures, Communes, Quartiers). Idempotent."

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge-inconnue",
            action="store_true",
            help="Supprime les entrées 'Inconnue' si elles ne sont pas référencées",
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Chemin vers un dataset externe (JSON hiérarchique ou CSV colonnes: region,prefecture,commune,quarter)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Source selection order: --file > json in data dir > DEFAULT_DATA
        dataset = None
        file_arg = options.get('file')
        if file_arg:
            p = Path(file_arg)
            if not p.exists():
                raise CommandError(f"Fichier introuvable: {file_arg}")
            if p.suffix.lower() == '.json':
                with p.open('r', encoding='utf-8') as f:
                    dataset = json.load(f)
            elif p.suffix.lower() == '.csv':
                # Build hierarchical dataset from CSV rows
                dataset = {}
                with p.open('r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    # expected headers: region,prefecture,commune,quarter
                    for row in reader:
                        region_name = (row.get('region') or '').strip()
                        prefecture_name = (row.get('prefecture') or '').strip()
                        commune_name = (row.get('commune') or '').strip()
                        quarter_name = (row.get('quarter') or '').strip()
                        if not (region_name and prefecture_name and commune_name):
                            # Skip incomplete rows
                            continue
                        dataset.setdefault(region_name, {"Préfectures": {}})
                        dataset[region_name]["Préfectures"].setdefault(prefecture_name, {"Communes": {}})
                        dataset[region_name]["Préfectures"][prefecture_name]["Communes"].setdefault(commune_name, [])
                        if quarter_name:
                            dataset[region_name]["Préfectures"][prefecture_name]["Communes"][commune_name].append(quarter_name)
            else:
                raise CommandError("Extension non supportée. Utilisez .json ou .csv")
        if dataset is None:
            data_path = Path(__file__).resolve().parents[2] / 'data' / 'guinea_locations.json'
            if data_path.exists():
                try:
                    with data_path.open('r', encoding='utf-8') as f:
                        dataset = json.load(f)
                except Exception:
                    dataset = DEFAULT_DATA
            else:
                dataset = DEFAULT_DATA

        created_regions = created_prefectures = created_communes = created_quarters = 0

        for region_name, rdata in dataset.items():
            region, created = Region.objects.get_or_create(name=region_name)
            created_regions += int(created)
            for pref_name, pdata in (rdata.get("Préfectures") or {}).items():
                prefecture, created = Prefecture.objects.get_or_create(name=pref_name, region=region)
                created_prefectures += int(created)
                for com_name, qdata in (pdata.get("Communes") or {}).items():
                    commune, created = Commune.objects.get_or_create(name=com_name, prefecture=prefecture)
                    created_communes += int(created)
                    for quarter_name in qdata or []:
                        quarter, created = Quarter.objects.get_or_create(name=quarter_name, commune=commune)
                        created_quarters += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"Chargement terminé: +{created_regions} régions, +{created_prefectures} préfectures, +{created_communes} communes, +{created_quarters} quartiers"
        ))

        if options.get("purge_inconnue"):
            removed = 0
            # Ne supprime que si non référencé
            for Model in (Quarter, Commune, Prefecture, Region):
                qs = Model.objects.filter(name__iexact='Inconnue')
                for obj in qs:
                    if not obj._meta.relationships:
                        continue
                    # Vérifie les relations sortantes
                    has_refs = False
                    for rel in obj._meta.related_objects:
                        if rel.related_model.objects.filter(**{rel.field.name: obj}).exists():
                            has_refs = True
                            break
                    if not has_refs:
                        obj.delete()
                        removed += 1
            self.stdout.write(self.style.WARNING(f"Entrées 'Inconnue' supprimées: {removed}"))
