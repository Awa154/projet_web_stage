# Generated by Django 4.0 on 2024-08-27 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_affectation_entreprise_simple'),
    ]

    operations = [
        migrations.AddField(
            model_name='departement',
            name='est_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='entreprise',
            name='est_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='est_active',
            field=models.BooleanField(default=True),
        ),
    ]