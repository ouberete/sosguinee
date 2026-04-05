from django.db import migrations


def null_quarter(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE loss_alert SET quarter = NULL")
    except Exception:
        pass
    try:
        cursor.execute("UPDATE funding_request SET quarter = NULL")
    except Exception:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('page', '0036b_make_quarter_nullable_pre_fk'),
    ]

    operations = [
        migrations.RunPython(null_quarter, reverse_code=migrations.RunPython.noop),
    ]

