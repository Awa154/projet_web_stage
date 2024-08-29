# Generated by Django 4.0 on 2024-08-20 13:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_entreprise_site_web'),
    ]

    operations = [
        migrations.AddField(
            model_name='contrat',
            name='entreprise',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.entreprise'),
        ),
        migrations.AddField(
            model_name='departement',
            name='entreprise',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.entreprise'),
        ),
        migrations.AddField(
            model_name='salarie',
            name='department_assigner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.departement'),
        ),
        migrations.AlterField(
            model_name='admin',
            name='travail_chez',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.entreprise'),
        ),
        migrations.DeleteModel(
            name='ContratSalarie',
        ),
    ]
