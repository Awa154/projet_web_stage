# Generated by Django 4.0 on 2024-08-02 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_role_acce_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='acce_page',
            field=models.CharField(blank=True, choices=[('SPAD', 'Page super administrateur'), ('AD', 'Page administrateur'), ('SA', 'Page salarié'), ('EN', 'Page des partenaires'), ('CL', 'Page des clients')], max_length=60, null=True),
        ),
    ]
