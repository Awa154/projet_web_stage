from datetime import date, timedelta
import re
from django.db import models
from django.dispatch import receiver
from django.forms import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.timezone import now
    
class Role(models.Model):
    ACCE_PAGE = (
        ('GE', 'Gestionnaire'),
        ('AD', 'Page administrateur'),
        ('SA', 'Page salarié'),
        ('EN', 'Page des partenaires'),
        ('CL', 'Page des clients'),
    )
    nom_role = models.CharField(max_length=50, unique=True)
    acce_page=models.CharField(max_length=60,choices=ACCE_PAGE, null=True, blank=True)
    est_active = models.BooleanField(default=True)

class Compte(models.Model):
    SEXE_CHOICES = (
        ('H', 'Homme'),
        ('F', 'Femme'),
    )
    nom_utilisateur = models.CharField(max_length=100)
    mot_de_passe = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, null=True, blank=True)
    email = models.EmailField(max_length=200, unique=True, null=True, blank=True)
    adresse = models.CharField(max_length=100, null=True, blank=True)
    telephone = PhoneNumberField(unique=True,null=True, blank=True)
    date_creer = models.DateTimeField(default=timezone.now)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Champ pour indiquer si le compte est actif

    def __str__(self):
        return self.email

class Entreprise(models.Model):
    type_entreprise = models.CharField(max_length=100, default="Mon entreprise")
    nom_entreprise = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True,null=True)
    site_web = models.URLField(max_length=255, blank=True, null=True)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='entreprise')
    est_active = models.BooleanField(default=True)
    
class Partenaire(models.Model):
    compte = models.OneToOneField(Compte, on_delete=models.CASCADE)
    entreprise = models.OneToOneField(Entreprise, on_delete=models.CASCADE)
    nom_agent_entreprise= models.CharField(max_length=100, default="Aucun")
    prenom_agent_entreprise=models.CharField(max_length=200, default="Aucun")
    poste_agent= models.CharField(max_length=200, default="Agent")
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='compte_partenaire')
    
class Admin(models.Model):
    compte = models.OneToOneField(Compte, on_delete=models.CASCADE)
    nom_admin = models.CharField(max_length=100)
    prenom_admin = models.CharField(max_length=150)
    fonction_admin= models.CharField(max_length=150, default="Aucun")
    travail_chez = models.ForeignKey(Entreprise, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nom_admin} {self.prenom_admin}"
    
class Client(models.Model):
    compte = models.OneToOneField(Compte, on_delete=models.CASCADE, null=True, blank=True)
    type_client = models.CharField(max_length=100)
    entreprise_affilier = models.ForeignKey(Entreprise, on_delete=models.SET_NULL, null=True, blank=True)
    nom_client = models.CharField(max_length=100)
    prenom_client = models.CharField(max_length=200)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='compte_client')

class Departement(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, null=True, blank=True)
    nom_dep = models.CharField(max_length=100, unique=True)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='departement')
    est_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nom_dep 
    
class Salarie(models.Model):
    compte = models.OneToOneField(Compte, on_delete=models.CASCADE)
    nom_salarie = models.CharField(max_length=100)
    prenom_salarie = models.CharField(max_length=200)
    department_assigner = models.ForeignKey(Departement, on_delete=models.CASCADE, null=True, blank=True)
    dateNaissance = models.DateField(null=True, blank=True)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='compte_salarie')
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.dateNaissance.year - ((today.month, today.day) < (self.dateNaissance.month, self.dateNaissance.day))

class Competence(models.Model):
    salarie = models.ForeignKey(Salarie, on_delete=models.CASCADE)
    competence = models.CharField(max_length=100,null=True, blank=True)
    
class Contrat(models.Model):
    fait_le = models.DateTimeField(default=timezone.now)
    nom_identifiant_contrat=models.CharField(max_length=100, null=True, blank=True)
    type_contrat = models.CharField(max_length=100)
    date_debut = models.DateField()
    date_fin = models.DateField()
    detail=models.TextField(blank=True)
    fonction_salarie= models.CharField(max_length=100, null=True, blank=True)
    salarie = models.ForeignKey(Salarie, on_delete=models.CASCADE)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.SET_NULL, null=True, blank=True)
    est_terminer = models.BooleanField(default=False)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='contrat')
    
    def get_employeur(self):
        if self.affectation_set.exists():
            affectation = self.affectation_set.first()
            if affectation.client:
                return f"{affectation.client.nom_client} {affectation.client.prenom_client}"
            elif affectation.entreprise_partenaire:
                return affectation.entreprise_partenaire.entreprise.nom_entreprise
            elif affectation.entreprise_simple:
                return affectation.entreprise_simple.nom_entreprise
        # Si pas d'affectation, alors c'est un contrat simple
        return self.entreprise.nom_entreprise if self.entreprise else "Non défini"

class Affectation(models.Model):
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE)
    entreprise_partenaire = models.ForeignKey(Partenaire, on_delete=models.CASCADE, null=True, blank=True)
    entreprise_simple = models.ForeignKey(Entreprise, on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='affectation')

class Doc_contrat(models.Model):
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE)
    titre_contrat= models.CharField(max_length=200)
    soustitre_contrat= models.CharField(max_length=200)
    text_intro_contrat= models.TextField(null=True, blank=True)
    detail_contrat = models.TextField(null=True, blank=True)
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='doc_contrat')
    
class Article(models.Model):
    doc_contrat = models.ForeignKey(Doc_contrat, on_delete=models.CASCADE)
    titre_article = models.CharField(max_length=200)
    detail_article = models.TextField(null=True, blank=True)

class FicheDePaieSalarie(models.Model):
    fait_le = models.DateTimeField(default=timezone.now)
    periode = models.DateField(null=True, blank=True)
    nom_identifiant_paie=models.CharField(max_length=100, null=True, blank=True)
    salarie = models.ForeignKey(Salarie, on_delete=models.CASCADE, null=True, blank=True)
    detail=models.TextField(blank=True)
    salaire_base = models.FloatField(null=True, blank=True)
    jour_non_travailler= models.IntegerField(null=True, blank=True)
    taux_journalier = models.FloatField(null=True, blank=True)
    salaire_mensuel = models.FloatField(null=True, blank=True)
    heure_supp= models.IntegerField(null=True, blank=True)
    taux_heure_supp = models.FloatField(null=True, blank=True)
    nbre_jour_travail= models.IntegerField(null=True, blank=True)
    travail_nuit= models.IntegerField(null=True, blank=True)
    nbre_jour_conger= models.IntegerField(null=True, blank=True)
    prime_ancien= models.FloatField(null=True, blank=True)
    prime_salissure= models.FloatField(null=True, blank=True)
    prime_panier= models.FloatField(null=True, blank=True)
    indemnite_depl= models.FloatField(null=True, blank=True)
    retenue_css= models.FloatField(null=True, blank=True)
    retenue_amu= models.FloatField(null=True, blank=True)
    salaire_net = models.FloatField(null=True, blank=True)
    est_payer = models.BooleanField(default=False) 
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='paie')
    
class FicheDePaieAffectation(models.Model):
    fait_le = models.DateTimeField(default=timezone.now)
    nom_identifiant_paie_affectation=models.CharField(max_length=100, null=True, blank=True)
    echeance = models.DateField(null=True, blank=True)
    affectation = models.ForeignKey(Affectation, on_delete=models.CASCADE)
    detail=models.TextField(blank=True)
    heure_travail= models.IntegerField(null=True, blank=True)
    taux_heure_travail = models.FloatField(null=True, blank=True)
    heure_supp= models.IntegerField(null=True, blank=True)
    taux_heure_supp = models.FloatField(null=True, blank=True)
    nbre_jour_travail= models.IntegerField(null=True, blank=True)
    prime_salissure= models.FloatField(null=True, blank=True)
    indemnite_depl= models.FloatField(null=True, blank=True)
    montant_de_base = models.FloatField(null=True, blank=True)
    montant_total = models.FloatField(null=True, blank=True)
    est_payer = models.BooleanField(default=False) 
    creer_par = models.ForeignKey(Compte, on_delete=models.SET_NULL, null=True, related_name='paie_affectation')

class Demande(models.Model):
    STATUT_CHOICES = (
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('REFUSE', 'Refusé'),
    )
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE)
    titre = models.CharField(max_length=200)
    details = models.TextField()    
    fait_le= models.DateTimeField(default=timezone.now)
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='EN_ATTENTE')
    
class EmailSettings(models.Model):
    host = models.CharField(max_length=255)
    port = models.IntegerField(default=587)
    host_user = models.CharField(max_length=255)
    host_password = models.CharField(max_length=255)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)

    def __str__(self):
        return f"Email Settings: {self.host}"
    
class EnregistrerPDF(models.Model):
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE, null=True, blank=True)
    fiche_de_paie_affectation = models.ForeignKey(FicheDePaieAffectation, on_delete=models.CASCADE, null=True, blank=True)
    fiche_de_paie = models.ForeignKey(FicheDePaieSalarie, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='pdfs/')
    creer_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PDF for {self.contrat.nom_identifiant_contrat} - {self.created_at}"

