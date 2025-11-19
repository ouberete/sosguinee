from django.db import migrations


def backfill_locations(apps, schema_editor):
    # Get historical models
    Region = apps.get_model('page', 'Region')
    Prefecture = apps.get_model('page', 'Prefecture')
    Commune = apps.get_model('page', 'Commune')
    Quarter = apps.get_model('page', 'Quarter')

    # Create or get placeholders
    region, _ = Region.objects.get_or_create(name='Inconnue')
    prefecture, _ = Prefecture.objects.get_or_create(name='Inconnue', region=region)
    commune, _ = Commune.objects.get_or_create(name='Inconnue', prefecture=prefecture)

    connection = schema_editor.connection
    cursor = connection.cursor()

    def coerce_table(table_name):
        # 1) Collect distinct legacy text values currently sitting in quarter_id
        try:
            cursor.execute(f"SELECT DISTINCT quarter_id FROM {table_name} WHERE quarter_id IS NOT NULL")
            rows = cursor.fetchall()
        except Exception:
            rows = []

        text_quarters = []
        for (val,) in rows:
            # In SQLite, legacy values will be TEXT; we consider non-integers as legacy names
            try:
                int(val)
            except Exception:
                if isinstance(val, str) and val.strip():
                    text_quarters.append(val.strip())

        # 2) Ensure Quarter rows exist for each legacy text value under placeholder commune
        name_to_id = {}
        for name in set(text_quarters):
            q_obj, _ = Quarter.objects.get_or_create(name=name, commune=commune)
            name_to_id[name] = q_obj.id

        # 3) Update rows to use new FK ids and fill missing higher-level FKs
        for name, qid in name_to_id.items():
            try:
                cursor.execute(
                    f"UPDATE {table_name} SET quarter_id = ?, commune_id = ?, prefecture_id = ?, region_id = ? "
                    f"WHERE quarter_id = ?",
                    [qid, commune.id, prefecture.id, region.id, name]
                )
            except Exception:
                # Ignore per-row errors to avoid blocking migration; constraints will catch leftovers
                pass

        # 4) Set default placeholders for rows with NULL location fields
        try:
            cursor.execute(
                f"UPDATE {table_name} SET region_id = ? WHERE region_id IS NULL",
                [region.id]
            )
            cursor.execute(
                f"UPDATE {table_name} SET prefecture_id = ? WHERE prefecture_id IS NULL",
                [prefecture.id]
            )
            cursor.execute(
                f"UPDATE {table_name} SET commune_id = ? WHERE commune_id IS NULL",
                [commune.id]
            )
        except Exception:
            pass

    # Coerce both tables
    coerce_table('funding_request')
    coerce_table('loss_alert')


def noop_reverse(apps, schema_editor):
    # No-op reverse migration
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('page', '0037_remove_fundingrequest_city_remove_lossalert_city_and_more'),
        ('page', '0036c_null_out_quarter_before_fk'),
    ]

    operations = [
        migrations.RunPython(backfill_locations, noop_reverse),
    ]
