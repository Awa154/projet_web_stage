# Generated by Django 4.0 on 2024-08-01 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_remove_compte_photo_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departement',
            name='nom_dep',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='role',
            name='nom_role',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
