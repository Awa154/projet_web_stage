# Generated by Django 4.0 on 2024-08-21 13:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_contrat_entreprise_departement_entreprise_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contrat',
            name='delai_alerte_exp',
        ),
    ]
