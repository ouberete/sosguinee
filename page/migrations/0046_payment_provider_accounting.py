from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("page", "0045_donation_is_anonymous_fundpayment_is_anonymous"),
    ]

    operations = [
        migrations.AddField(
            model_name="donation",
            name="received_amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True, verbose_name="Montant net reçu"),
        ),
        migrations.AddField(
            model_name="donation",
            name="fees",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True, verbose_name="Frais de paiement"),
        ),
        migrations.AddField(
            model_name="donation",
            name="provider_transaction_id",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name="ID transaction prestataire"),
        ),
        migrations.AddField(
            model_name="donation",
            name="provider_payment_method",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Moyen de paiement prestataire"),
        ),
        migrations.AddField(
            model_name="donation",
            name="provider_currency",
            field=models.CharField(blank=True, default="GNF", max_length=10, verbose_name="Devise prestataire"),
        ),
        migrations.AddField(
            model_name="fundpayment",
            name="received_amount",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True, verbose_name="Montant net reçu"),
        ),
        migrations.AddField(
            model_name="fundpayment",
            name="fees",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True, verbose_name="Frais de paiement"),
        ),
        migrations.AddField(
            model_name="fundpayment",
            name="provider_transaction_id",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name="ID transaction prestataire"),
        ),
        migrations.AddField(
            model_name="fundpayment",
            name="provider_payment_method",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Moyen de paiement prestataire"),
        ),
        migrations.AddField(
            model_name="fundpayment",
            name="provider_currency",
            field=models.CharField(blank=True, default="GNF", max_length=10, verbose_name="Devise prestataire"),
        ),
    ]