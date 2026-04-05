from django.db import migrations
import uuid

def backfill_public_id(apps, schema_editor):
    for model_name in ['SubscriptionPlan', 'UserSubscription', 'SubscriptionPayment']:
        Model = apps.get_model('accounts', model_name)
        for obj in Model.objects.filter(public_id__isnull=True).iterator(chunk_size=500):
            obj.public_id = uuid.uuid4()
            obj.save(update_fields=['public_id'])

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_subscriptionpayment_public_id_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_public_id, reverse_code=migrations.RunPython.noop),
    ]
