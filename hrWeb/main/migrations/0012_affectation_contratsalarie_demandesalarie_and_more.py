# Generated by Django 4.0 on 2024-08-16 17:19

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_remove_fichedepaie_dateemission_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Affectation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='ContratSalarie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee_exp', models.PositiveIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DemandeSalarie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=200)),
                ('details', models.TextField()),
                ('competences_recherchees', models.CharField(max_length=255)),
                ('fait_le', models.DateTimeField(default=django.utils.timezone.now)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('VALIDÉ', 'Validé'), ('REFUSÉ', 'Refusé')], default='EN_ATTENTE', max_length=10)),
                ('compte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.compte')),
            ],
        ),
        migrations.CreateModel(
            name='FicheDePaieAffectation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fait_le', models.DateTimeField(default=django.utils.timezone.now)),
                ('nom_identifiant_paie_affectation', models.CharField(blank=True, max_length=100, null=True)),
                ('echeance', models.DateField(blank=True, null=True)),
                ('detail', models.TextField(blank=True)),
                ('montant', models.FloatField(blank=True, null=True)),
                ('est_payer', models.BooleanField(default=False)),
                ('affectation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.affectation')),
                ('creer_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paie_affectation', to='main.compte')),
            ],
        ),
        migrations.CreateModel(
            name='FicheDePaieSalarie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fait_le', models.DateTimeField(default=django.utils.timezone.now)),
                ('periode', models.DateField(blank=True, null=True)),
                ('nom_identifiant_paie', models.CharField(blank=True, max_length=100, null=True)),
                ('detail', models.TextField(blank=True)),
                ('salaire_base', models.FloatField(blank=True, null=True)),
                ('jour_non_travailler', models.IntegerField(blank=True, null=True)),
                ('taux_journalier', models.FloatField(blank=True, null=True)),
                ('salaire_mensuel', models.FloatField(blank=True, null=True)),
                ('heure_supp', models.IntegerField(blank=True, null=True)),
                ('taux_heure_supp', models.FloatField(blank=True, null=True)),
                ('nbre_jour_travail', models.IntegerField(blank=True, null=True)),
                ('travail_nuit', models.IntegerField(blank=True, null=True)),
                ('nbre_jour_conger', models.IntegerField(blank=True, null=True)),
                ('prime_ancien', models.FloatField(blank=True, null=True)),
                ('prime_salissure', models.FloatField(blank=True, null=True)),
                ('prime_panier', models.FloatField(blank=True, null=True)),
                ('indemnite_depl', models.FloatField(blank=True, null=True)),
                ('retenue_css', models.FloatField(blank=True, null=True)),
                ('retenue_amu', models.FloatField(blank=True, null=True)),
                ('salaire_net', models.FloatField(blank=True, null=True)),
                ('est_payer', models.BooleanField(default=False)),
                ('creer_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paie', to='main.compte')),
            ],
        ),
        migrations.CreateModel(
            name='Partenaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_agent_entreprise', models.CharField(default='Aucun', max_length=100)),
                ('prenom_agent_entreprise', models.CharField(default='Aucun', max_length=200)),
                ('poste_agent', models.CharField(default='Agent', max_length=200)),
                ('compte', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.compte')),
                ('creer_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compte_partenaire', to='main.compte')),
            ],
        ),
        migrations.RemoveField(
            model_name='fichedepaie',
            name='creer_par',
        ),
        migrations.RemoveField(
            model_name='fichedepaie',
            name='entreprise',
        ),
        migrations.RemoveField(
            model_name='fichedepaie',
            name='salarie',
        ),
        migrations.RemoveField(
            model_name='client',
            name='association_key',
        ),
        migrations.RemoveField(
            model_name='client',
            name='poste_occupe',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='client',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='entreprise',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='heures_travail',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='jours_travail',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='mode_paiement',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='salaire_mensuel',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='taux_horaire',
        ),
        migrations.RemoveField(
            model_name='contrat',
            name='taux_journalier',
        ),
        migrations.RemoveField(
            model_name='entreprise',
            name='compte',
        ),
        migrations.RemoveField(
            model_name='entreprise',
            name='nom_agent_entreprise',
        ),
        migrations.RemoveField(
            model_name='entreprise',
            name='poste_agent',
        ),
        migrations.RemoveField(
            model_name='entreprise',
            name='prenom_agent_entreprise',
        ),
        migrations.RemoveField(
            model_name='salarie',
            name='annee_exp',
        ),
        migrations.RemoveField(
            model_name='salarie',
            name='departement',
        ),
        migrations.AddField(
            model_name='admin',
            name='travail_chez',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.entreprise'),
        ),
        migrations.AddField(
            model_name='contrat',
            name='delai_alerte_exp',
            field=models.IntegerField(default=30, help_text="Délai en jours avant l'expiration pour déclencher une alerte."),
        ),
        migrations.AddField(
            model_name='contrat',
            name='detail',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contrat',
            name='nom_identifiant_contrat',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='doc_contrat',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='doc_contrat', to='main.compte'),
        ),
        migrations.AddField(
            model_name='entreprise',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='entreprise',
            name='site_web',
            field=models.URLField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='client',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compte_client', to='main.compte'),
        ),
        migrations.AlterField(
            model_name='client',
            name='type_client',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='contrat',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contrat', to='main.compte'),
        ),
        migrations.AlterField(
            model_name='departement',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='departement', to='main.compte'),
        ),
        migrations.AlterField(
            model_name='entreprise',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entreprise', to='main.compte'),
        ),
        migrations.AlterField(
            model_name='entreprise',
            name='type_entreprise',
            field=models.CharField(default='Mon entreprise', max_length=100),
        ),
        migrations.AlterField(
            model_name='salarie',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='compte_salarie', to='main.compte'),
        ),
        migrations.DeleteModel(
            name='DemandeEmploye',
        ),
        migrations.DeleteModel(
            name='FicheDePaie',
        ),
        migrations.AddField(
            model_name='partenaire',
            name='entreprise',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='main.entreprise'),
        ),
        migrations.AddField(
            model_name='fichedepaiesalarie',
            name='salarie',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.salarie'),
        ),
        migrations.AddField(
            model_name='contratsalarie',
            name='contrat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.contrat'),
        ),
        migrations.AddField(
            model_name='contratsalarie',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contrat_salarie', to='main.compte'),
        ),
        migrations.AddField(
            model_name='contratsalarie',
            name='departement',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.departement'),
        ),
        migrations.AddField(
            model_name='contratsalarie',
            name='entreprise',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.entreprise'),
        ),
        migrations.AddField(
            model_name='affectation',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.client'),
        ),
        migrations.AddField(
            model_name='affectation',
            name='contrat',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.contrat'),
        ),
        migrations.AddField(
            model_name='affectation',
            name='creer_par',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='affectation', to='main.compte'),
        ),
        migrations.AddField(
            model_name='affectation',
            name='entreprise_partenaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.partenaire'),
        ),
    ]