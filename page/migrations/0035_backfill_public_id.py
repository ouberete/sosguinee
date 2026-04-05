from django.db import migrations
import uuid

def backfill_public_id(apps, schema_editor):
    model_names = [
        'Comment','Donation','EmailContent','FundingRequest','FundingRequestNotification','FundingRequestStatus',
        'FundingType','FundPayment','LossAlert','LossAlertNotification','LossAlertStatus','LossAlertType',
        'MessageContact','OptionalAlertDoc','OptionalFundingDoc','UserDetails'
    ]
    for name in model_names:
        Model = apps.get_model('page', name)
        # Iterate in chunks to avoid memory spikes on large tables
        qs = Model.objects.filter(public_id__isnull=True)
        for obj in qs.iterator(chunk_size=500):
            obj.public_id = uuid.uuid4()
            obj.save(update_fields=['public_id'])

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('page', '0034_comment_public_id_donation_public_id_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_public_id, reverse_code=noop),
    ]
