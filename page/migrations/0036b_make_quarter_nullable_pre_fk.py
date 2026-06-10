from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('page', '0036_alter_comment_public_id_alter_donation_public_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lossalert',
            name='quarter',
            field=models.CharField(max_length=255, null=True, blank=True, verbose_name='Quartier'),
        ),
        migrations.AlterField(
            model_name='fundingrequest',
            name='quarter',
            field=models.CharField(max_length=255, null=True, blank=True, verbose_name='Quartier'),
        ),
    ]

