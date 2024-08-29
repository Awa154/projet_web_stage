import re
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.urls import reverse
from datetime import datetime
from django.http import JsonResponse
from django.template.loader import get_template
from .models import *
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.contrib.auth.hashers import check_password, make_password
import random, string, datetime
from django.db.models import Q, Count
import os
from django.core.files import File
from io import BytesIO
import pdfkit
config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

# Create your views here.

#Fonction pour retourner la vue vers la page d'accueil de l'admin
def home(request):
    return render(request,'pages/home/home.html')

#Fonction pour retourner la vue vers la page d'accueil de l'admin
def home_admin(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier si l'utilisateur a accès à la page admin
    if compte.role.acce_page in ['AD', 'GE']:  # Si c'est un admin ou un gestionnaire
        try:
            admin = Admin.objects.get(compte=compte)
            # Statistiques
            total_salaries = Compte.objects.select_related('role').filter(role__acce_page='SA').count()
            total_partenaires = Compte.objects.select_related('role').filter(role__acce_page='EN').count()
            total_clients = Compte.objects.select_related('role').filter(role__acce_page='CL').count()
            total_contrats = Contrat.objects.all().count()

            context = {
                'total_salaries': total_salaries,
                'total_partenaires': total_partenaires,
                'total_clients': total_clients,
                'total_contrats': total_contrats,
            }
            return render(request, 'pages/admin/compte/home.html', context)
        except Admin.DoesNotExist:
            messages.error(request, "Aucun administrateur associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à ce tableau de bord.")
        return redirect('home')

#Fonction pour retourner la vue vers la page d'accueil
def home_salarie(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un salarié
    if compte.role.acce_page == 'SA':  # Si c'est un salarié
        try:
            salarie = Salarie.objects.get(compte=compte)

            # Compter les contrats en cours et terminés du salarié
            contrats_en_cours = Contrat.objects.filter(salarie=salarie, est_terminer=False).count()
            contrats_termines = Contrat.objects.filter(salarie=salarie, est_terminer=True).count()

            # Compter les fiches de paie payées et impayées du salarié
            fiches_paie_payees = FicheDePaieSalarie.objects.filter(salarie=salarie, est_payer=True).count()
            fiches_paie_impayees = FicheDePaieSalarie.objects.filter(salarie=salarie, est_payer=False).count()

            context = {
                'contrats_en_cours': contrats_en_cours,
                'contrats_termines': contrats_termines,
                'fiches_paie_payees': fiches_paie_payees,
                'fiches_paie_impayees': fiches_paie_impayees,
            }

            return render(request, 'pages/salarie/compte/home.html', context)
        except Salarie.DoesNotExist:
            messages.error(request, "Aucun salarié associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à ce tableau de bord.")
        return redirect('home')
    
def liste_contrats_salarie(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un salarié
    if compte.role.acce_page == 'SA':  # Si c'est un salarié
        try:
            salarie = Salarie.objects.get(compte=compte)

            # Récupérer la liste des contrats en cours et terminer pour ce salarié
            contrats_en_cours = Contrat.objects.filter(
                salarie=salarie,
                est_terminer=False
            ).select_related('contratsalarie').prefetch_related('affectation_set')
            
            contrats_terminer = Contrat.objects.filter(
                salarie=salarie,
                est_terminer=True
            ).select_related('contratsalarie').prefetch_related('affectation_set')

            context = {
                'contrats_en_cours': contrats_en_cours,
                'contrats_terminer':contrats_terminer,
                ' salarie ': salarie ,
            }

            return render(request, 'pages/salarie/actions/liste_contrats_salarie.html', context)
        except Salarie.DoesNotExist:
            messages.error(request, "Aucun salarié associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('home')

def liste_fiches_de_paie_salarie(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un salarié
    if compte.role.acce_page == 'SA':  # Si c'est un salarié
        try:
            salarie = Salarie.objects.get(compte=compte)

            # Récupérer la liste des fiches de paie payées et impayées pour ce salarié
            fiches_paie_payees = FicheDePaieSalarie.objects.filter(
                salarie=salarie,
                est_payer=True
            )
            fiches_paie_impayees = FicheDePaieSalarie.objects.filter(
                salarie=salarie,
                est_payer=False
            )

            context = {
                'fiches_paie_payees': fiches_paie_payees,
                'fiches_paie_impayees': fiches_paie_impayees,
            }

            return render(request, 'pages/salarie/actions/liste_fiches_paie_salarie.html', context)
        except Salarie.DoesNotExist:
            messages.error(request, "Aucun salarié associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('home')


#Fonction pour retourner la vue vers la page d'accueil
def home_partenaire(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un partenaire
    if compte.role.acce_page == 'EN':  # Si c'est un partenaire
        try:
            partenaire = Partenaire.objects.get(compte=compte)

            # Compter les demandes du partenaire
            total_demandes = Demande.objects.filter(compte=compte).count()

            # Compter les contrats liés à ce partenaire après affectation
            total_contrats = Affectation.objects.filter(entreprise_partenaire=partenaire).count()

            # Compter les fiches de paie payées et impayées après affectation pour ce partenaire
            fiches_paie_payees = FicheDePaieAffectation.objects.filter(affectation__entreprise_partenaire=partenaire, est_payer=True).count()
            fiches_paie_impayees = FicheDePaieAffectation.objects.filter(affectation__entreprise_partenaire=partenaire, est_payer=False).count()

            context = {
                'total_demandes': total_demandes,
                'total_contrats': total_contrats,
                'fiches_paie_payees': fiches_paie_payees,
                'fiches_paie_impayees': fiches_paie_impayees,
            }

            return render(request, 'pages/partenaire/compte/home.html', context)
        except Partenaire.DoesNotExist:
            messages.error(request, "Aucun partenaire associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à ce tableau de bord.")
        return redirect('home')
    
def liste_salaries_contrats_partenaire(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un partenaire
    if compte.role.acce_page == 'EN':  # Si c'est un partenaire
        try:
            partenaire = Partenaire.objects.get(compte=compte)

            # Récupérer la liste des salariés avec des contrats en cours via des affectations
            partenaire_salaries_en_cour = Salarie.objects.filter(
                contrat__est_terminer=False,
                contrat__affectation__entreprise_partenaire=partenaire
            ).distinct()
            
            partenaire_salaries_terminer = Salarie.objects.filter(
                contrat__est_terminer=True,
                contrat__affectation__entreprise_partenaire=partenaire
            ).distinct()

            context = {
                'partenaire_salaries_en_cour': partenaire_salaries_en_cour,
                'partenaire_salaries_terminer': partenaire_salaries_terminer,
            }

            return render(request, 'pages/entreprise/liste_salaries_contrats_en_cours.html', context)
        except Partenaire.DoesNotExist:
            messages.error(request, "Aucun partenaire associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('home')

def liste_fiches_de_paie_partenaire(request):
    compte = request.user

    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')

    if compte.role.acce_page == 'EN':  # Si c'est un partenaire
        try:
            partenaire = Partenaire.objects.get(compte=compte)

            # Récupérer la liste des fiches de paie payées et impayées pour ce partenaire
            fiches_paie_payees = FicheDePaieAffectation.objects.filter(
                affectation__entreprise_partenaire=partenaire,
                est_payer=True
            ).select_related('affectation__contrat', 'affectation__contrat__salarie')

            fiches_paie_impayees = FicheDePaieAffectation.objects.filter(
                affectation__entreprise_partenaire=partenaire,
                est_payer=False
            ).select_related('affectation__contrat', 'affectation__contrat__salarie')

            context = {
                'fiches_paie_payees': fiches_paie_payees,
                'fiches_paie_impayees': fiches_paie_impayees,
            }

            return render(request, 'pages/entreprise/liste_fiches_paie.html', context)
        except Partenaire.DoesNotExist:
            messages.error(request, "Aucun partenaire associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('home')

#Fonction pour retourner la vue vers la page d'accueil
def home_client(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un client
    if compte.role.acce_page == 'CL':  # Si c'est un client
        try:
            client = Client.objects.get(compte=compte)

            # Compter les demandes du client
            total_demandes = Demande.objects.filter(compte=compte).count()

            # Compter les contrats liés à ce client après affectation
            total_contrats = Affectation.objects.filter(client=client).count()

            # Compter les fiches de paie payées et impayées après affectation pour ce client
            fiches_paie_payees = FicheDePaieAffectation.objects.filter(affectation__client=client, est_payer=True).count()
            fiches_paie_impayees = FicheDePaieAffectation.objects.filter(affectation__client=client, est_payer=False).count()

            context = {
                'total_demandes': total_demandes,
                'total_contrats': total_contrats,
                'fiches_paie_payees': fiches_paie_payees,
                'fiches_paie_impayees': fiches_paie_impayees,
            }

            return render(request, 'pages/client/compte/home.html', context)
        except Client.DoesNotExist:
            messages.error(request, "Aucun client associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à ce tableau de bord.")
        return redirect('home')

def liste_salaries_contrats_client(request):
    # Récupérer le compte de l'utilisateur connecté
    compte = request.user

    # Vérifier si le compte est bloqué
    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')  # Redirection vers la page de connexion ou une autre page appropriée

    # Vérifier le rôle pour s'assurer que c'est un client
    if compte.role.acce_page == 'CL':  # Si c'est un client
        try:
            client = Client.objects.get(compte=compte)

            # Récupérer la liste des salariés avec des contrats en cours via des affectations
            client_salaries = Salarie.objects.filter(
                contrat__affectation__client=client
            ).distinct()

            context = {
                'client_salaries': client_salaries,
            }

            return render(request, 'pages/client/liste_salaries_contrats_en_cours.html', context)
        except Client.DoesNotExist:
            messages.error(request, "Aucun client associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('home')

def liste_fiches_de_paie_client(request):
    compte = request.user

    if not compte.is_active:
        messages.error(request, "Votre compte est bloqué. Veuillez contacter l'administrateur.")
        return redirect('connexion')

    if compte.role.acce_page == 'CL':
        try:
            client = Client.objects.get(compte=compte)
            
            fiches_paie_payees = FicheDePaieAffectation.objects.filter(
                affectation__client=client,
                est_payer=True
            ).select_related('affectation__contrat', 'affectation__contrat__salarie')

            fiches_paie_impayees = FicheDePaieAffectation.objects.filter(
                affectation__client=client,
                est_payer=False
            ).select_related('affectation__contrat', 'affectation__contrat__salarie')

            context = {
                'fiches_paie_payees': fiches_paie_payees,
                'fiches_paie_impayees': fiches_paie_impayees,
            }

            return render(request, 'pages/client/liste_fiches_paie.html', context)
        except Client.DoesNotExist:
            messages.error(request, "Aucun client associé à ce compte.")
            return redirect('home')
    else:
        messages.error(request, "Vous n'avez pas accès à cette page.")
        return redirect('home')

# Vue permettant de générer automatiquement les noms d'utilisateur
def generer_nom_utilisateur(length=12):
    characters = string.ascii_letters
    while True:
        nom_utilisateur = ''.join(random.choice(characters) for i in range(length))
        if not Compte.objects.filter(nom_utilisateur=nom_utilisateur).exists():
            return nom_utilisateur

# Vue permettant de générer automatiquement les mots de passe
def generer_mot_de_passe(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def connexion(request):
    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        mot_de_passe = request.POST.get('mot_de_passe')

        # Initialiser les tentatives de connexion si non définies
        if 'login_attempts' not in request.session:
            request.session['login_attempts'] = 0
            request.session['lockout_time'] = None

        # Vérifier si l'utilisateur est verrouillé
        lockout_time = request.session.get('lockout_time')
        if lockout_time:
            lockout_time = datetime.datetime.fromisoformat(lockout_time)
            if timezone.now() < lockout_time:
                messages.error(request, "Nombre maximal de tentatives atteint. Veuillez réessayer après 30 secondes.")
                return render(request, "pages/auth/pages/login.html")

        try:
            compte = Compte.objects.get(nom_utilisateur=nom_utilisateur)
        except Compte.DoesNotExist:
            messages.error(request, "Nom d'utilisateur incorrect.")
            return redirect('connexion')

        if not compte.is_active:
            messages.error(request, "Votre compte est désactivé.")
            return render(request, "pages/auth/pages/login.html")

        if check_password(mot_de_passe, compte.mot_de_passe):
            request.session['user_id'] = compte.id
            request.session['user_nom_utilisateur'] = compte.nom_utilisateur

            # Réinitialiser les tentatives de connexion après une connexion réussie
            request.session['login_attempts'] = 0
            request.session['lockout_time'] = None

            if compte.role.acce_page == 'AD':
                return redirect('home_admin')
            elif compte.role.acce_page == 'SA':
                return redirect('home_salarie')
            elif compte.role.acce_page == 'EN':
                return redirect('home_partenaire')
            elif compte.role.acce_page == 'CL':
                return redirect('home_client')
            elif compte.role.acce_page == 'GE':
                return redirect('home_admin')
            else:
                messages.error(request, "Aucune page d'accès définie pour ce rôle.")
                return redirect('connexion')
        else:
            # Incrémenter les tentatives de connexion après un mot de passe incorrect
            request.session['login_attempts'] += 1
            if request.session['login_attempts'] >= 3:
                # Verrouiller l'utilisateur pendant 30 secondes
                request.session['lockout_time'] = (timezone.now() + datetime.timedelta(seconds=30)).isoformat()
                messages.error(request, "Nombre maximal de tentatives atteint. Veuillez réessayer après 30 secondes.")
            else:
                messages.error(request, "Mot de passe incorrect.")
            return redirect('connexion')
    else:
        return render(request, "pages/auth/login.html")
#Fonction de déconnexion
def deconnexion(request):
    # Supprimez la session de l'utilisateur
    if 'user_id' in request.session:
        del request.session['user_id']
    messages.success(request, "Vous êtes déconnecté.")
    return redirect('connexion')

#Fonction pour changer le mot de passe en cas d'oublie
def oublier_mot_de_passe(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = Compte.objects.get(email=email)
            temp_password = generer_mot_de_passe()
            user.mot_de_passe = make_password(generer_mot_de_passe)
            user.save()
            
            # Charger les paramètres d'email
            email_settings = load_email_settings()
            if email_settings:
                settings.EMAIL_HOST = email_settings['EMAIL_HOST']
                settings.EMAIL_PORT = email_settings['EMAIL_PORT']
                settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
                settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
                settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
                settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
            # Envoyer l'email avec les identifiants de connexion
            subject = "HrBridge"
            message = 'Votre mot de passe temporaire',f'Votre nouveau mot de passe temporaire est : {temp_password}\nVeuillez le changer après vous être connecté.',
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]

            if email:
                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )
            else:
                # Logique d'envoi par WhatsApp (à implémenter)
                pass

            messages.success(request, "Un mot de passe temporaire vous a été envoyé par email.")
            return redirect('connexion')
        except Compte.DoesNotExist:
            messages.error(request, "Aucun utilisateur trouvé avec cet email.")
            
    return render(request, "pages/auth/forget_password.html")

#Fonction pour modifier son mot de passe
def changer_mot_de_passe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = Compte.objects.get(id=user_id)

    if request.method == 'POST':
        ancien_mot_de_passe = request.POST.get('ancien_mot_de_passe')
        nouveau_mot_de_passe = request.POST.get('nouveau_mot_de_passe')
        confirmer_mot_de_passe = request.POST.get('confirmer_mot_de_passe')

        if not check_password(ancien_mot_de_passe, user.mot_de_passe):
            messages.error(request, "Le mot de passe actuel est incorrect.")
        elif nouveau_mot_de_passe != confirmer_mot_de_passe:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
        else:
            user.mot_de_passe = make_password(nouveau_mot_de_passe)
            user.save()
            messages.success(request, "Votre mot de passe à bien été changé")
            # Redirection basée sur l'accès de l'utilisateur
            if user.role.acce_page == "AD":
                return redirect('profile_admin')
            elif user.role.acce_page == "SA":
                return redirect('profile_salarie')
            elif user.role.acce_page == "EN":
                return redirect('profile_entreprise')
            elif user.role.acce_page == "CL":
                return redirect('profile_client')
            elif user.role.acce_page == "GE":
                return redirect('profile_salarie')
            else:
                return redirect('connexion')

    return render(request, 'pages/auth/change_password.html')

def annuler_changer_mot_de_passe(request):
    user_id = request.session.get('user_id')

    user = Compte.objects.get(id=user_id)
    # Redirection basée sur l'accès de l'utilisateur
    if user.role.acce_page == "AD":
        return redirect('profile_admin')
    elif user.role.acce_page == "SA":
        return redirect('profile_salarie')
    elif user.role.acce_page == "EN":
        return redirect('profile_entreprise')
    elif user.role.acce_page == "CL":
        return redirect('profile_client')
    elif user.role.acce_page == "GE":
        return redirect('profile_salarie')
    else:
        return redirect('connexion')

#Création de la vue pour créer un département
def creer_departement(request, entreprise_id):
    # Récupérer l'entreprise par son ID
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    
    if request.method == 'POST':
        nom_dep = request.POST.get('nom_dep')
        
        errors = {}
        # Vérifier si un département avec le même nom existe déjà pour cette entreprise
        if Departement.objects.filter(nom_dep=nom_dep, entreprise=entreprise).exists():
            errors['nom_dep'] = "Un département avec ce nom existe déjà dans cette entreprise."

        if errors:
            return render(request, 'pages/admin/departements/creer_departement.html', {
                'errors': errors,
                'nom_dep': nom_dep,
                'entreprise': entreprise,
            })

        try:
            # Créer le département associé à l'entreprise spécifique
            Departement.objects.create(nom_dep=nom_dep, entreprise=entreprise, creer_par=request.user)
            messages.success(request, 'Département créé avec succès.')
            return redirect(reverse('liste_departements', args=[entreprise_id]))
        except IntegrityError:
            messages.error(request, 'Erreur lors de la création du département.')
            
    return render(request, 'pages/admin/departements/creer_departement.html', {
        'entreprise': entreprise,
    })


#Fonction pour afficher la liste des départements
def liste_departements(request, entreprise_id):
    # Récupérer l'entreprise par son ID
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    
    # Vérifier le rôle de l'utilisateur
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les départements liés à cette entreprise et compter les salariés dans chaque département
        departements = Departement.objects.filter(entreprise=entreprise).annotate(
            nombre_salaries=Count('salarie__contrat')
        )
    else:
        # Filtrer les départements créés par l'utilisateur connecté pour l'entreprise spécifiée
        departements = Departement.objects.filter(creer_par=request.user, entreprise=entreprise).annotate(
            nombre_salaries=Count('salarie__contrat')
        )
    
    context = {
        'entreprise': entreprise,
        'departements': departements,
    }
    
    return render(request, 'pages/admin/departements/liste_departements.html', context)

#Fonction pour modifier un département
def modifier_departement(request, departement_id):
    departement = get_object_or_404(Departement, id=departement_id)

    # Vérifier si l'utilisateur a le droit de modifier ce département
    if departement.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de modifier ce département.")
        return redirect('liste_departements', entreprise_id=departement.entreprise.id)  # Rediriger vers la liste des départements de l'entreprise

    if request.method == 'POST':
        nom_dep = request.POST.get('nom_dep').strip()

        # Vérifier si un département avec ce nom existe déjà pour la même entreprise
        if Departement.objects.filter(nom_dep=nom_dep, entreprise=departement.entreprise).exclude(id=departement_id).exists():
            messages.error(request, 'Un département avec ce nom existe déjà pour cette entreprise.')
            return redirect('modifier_departement', departement_id=departement_id)  
            
        departement.nom_dep = nom_dep
        departement.save()
        messages.success(request, 'Le département a été mis à jour avec succès.')
        return redirect('liste_departements', entreprise_id=departement.entreprise.id)  # Rediriger vers la liste des départements après modification

    return render(request, 'pages/admin/departements/modifier_departement.html', {
        'departement': departement
    })

#Supprimer un département
def supprimer_departement(request, departement_id):
    departement = get_object_or_404(Departement, id=departement_id)

    # Vérifier si l'utilisateur a le droit de supprimer ce département
    if departement.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de supprimer ce département.")
        return redirect('liste_departements', entreprise_id=departement.entreprise.id)

    # Vérifier si le département contient des salariés
    if Salarie.objects.filter(department_assigner=departement).exists():
        messages.error(request, "Impossible de supprimer ce département car il contient des salariés.")
        return redirect('liste_departements', entreprise_id=departement.entreprise.id)

    # Supprimer partiellement le département en le désactivant
    departement.est_active = False
    departement.save()

    messages.success(request, "Le département a été désactivé avec succès.")
    return redirect('liste_departements', entreprise_id=departement.entreprise.id)

#Création de la vue pour créer un rôle
def creer_role(request):
    if request.method == 'POST':
        nom_role = request.POST['nom_role']
        acce_page = request.POST['acce_page']
        try:
            role = Role.objects.create(
                nom_role=nom_role, 
                acce_page=acce_page)
            messages.success(request, 'Rôle créé avec succès.')
            return redirect('liste_roles')
        except IntegrityError:
            messages.error(request, 'Un rôle avec ce nom existe déjà.')

    return render(request, 'pages/admin/roles/creer_role.html')

#Fonction pour retourner la vue vers la page de la liste des salariés
def liste_roles(request):
    roles = Role.objects.all()

    context = {
        'roles': roles,
    }
    return render(request,'pages/admin/roles/liste_roles.html', context)

# Modifier un rôle
def modifier_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    
    if request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de modifier ce rôle.")
        return redirect('liste_roles', role_id=role.id)

    if request.method == 'POST':
        nom_role = request.POST.get('nom_role')
        acce_page = request.POST.get('acce_page')
        
        # Vérifier si un rôle avec ce nom existe déjà
        if Role.objects.filter(nom_role=nom_role).exclude(id=role_id).exists():
            messages.error(request, 'Un rôle avec ce nom existe déjà.')
            return redirect('liste_roles')
            
        role.nom_role = nom_role
        role.acce_page = acce_page
        role.save()
        
        messages.success(request, 'Le rôle a été mis à jour avec succès.')
        return redirect('liste_roles') # Rediriger vers la liste des rôles après modification

    return render(request, 'pages/admin/roles/liste_roles.html', {'role': role})

#supprimer un rôle
def supprimer_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    
    if request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de supprimer ce rôle.")
        return redirect('liste_roles', role_id=role.id)
    
    # Vérifier si le rôle est associé à des comptes utilisateurs
    if Compte.objects.filter(role=role).exists():
        messages.error(request, "Impossible de supprimer ce rôle car il est associé à des comptes utilisateurs.")
        return redirect('liste_roles')
    
    # Suppression partielle : marquer le rôle comme inactif
    role.is_active = False
    role.save()

    messages.success(request, "Le rôle a été désactivé avec succès.")
    return redirect('liste_roles')


# Fonction pour ajouter un administrateur
def creer_admin(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_utilisateur = generer_nom_utilisateur()
        email = request.POST.get('email')
        sexe = request.POST.get('sexe')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        role_id = request.POST.get('role')
        mot_de_passe = generer_mot_de_passe()
        
        nom_admin = request.POST.get('nom_admin')
        prenom_admin = request.POST.get('prenom_admin')
        fonction_admin = request.POST.get('fonction_admin')
        travail_chez_id = request.POST.get('travail_chez')
        
        # Valider les données
        errors = {}
        
        # Vérifier l'unicité de l'email et du contact
        if Compte.objects.filter(email=email).exists():
            errors['email'] = "Un utilisateur avec cet email existe déjà."
        if Compte.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Un utilisateur avec ce contact existe déjà."
        
        # Validation des champs nom et prénom
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", nom_admin):
            errors['nom_admin'] = "Le nom de l'administrateur ne peut contenir que des lettres."
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", prenom_admin):
            errors['prenom_admin'] = "Le prénom de l'administrateur ne peut contenir que des lettres."
        
        # Validation de l'existence de l'entreprise associée
        try:
            travail_chez = Entreprise.objects.get(id=travail_chez_id)
        except Entreprise.DoesNotExist:
            errors['travail_chez'] = "L'entreprise sélectionnée n'existe pas."
        
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_admin.html', {
                'errors': errors,
                'email': email,
                'sexe': sexe,
                'adresse': adresse,
                'telephone': telephone,
                'nom_admin': nom_admin,
                'prenom_admin': prenom_admin,
                'fonction_admin': fonction_admin,
                'roles': Role.objects.all(),
                'entreprises': Entreprise.objects.all(),
            })
        
        # Création du compte
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            sexe=sexe,
            adresse=adresse,
            telephone=telephone,
            role=Role.objects.get(id=role_id),
        )
        
        # Création de l'administrateur
        Admin.objects.create(
            compte=compte,
            nom_admin=nom_admin,
            prenom_admin=prenom_admin,
            fonction_admin=fonction_admin,
            travail_chez=travail_chez,
        )
    
        # Charger les paramètres d'email
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']

        # Envoyer l'email avec les identifiants de connexion
        subject = "Bienvenue sur Stafflinker"
        message = f'''Bienvenue {nom_admin} {prenom_admin},

Votre compte a été créé.

Voici vos identifiants de connexion :

Nom d'utilisateur : {nom_utilisateur}
Mot de passe : {mot_de_passe}

Cordialement,
L'équipe Stafflinker'''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        if email:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
        else:
            # Logique d'envoi par WhatsApp (à implémenter)
            pass
        
        messages.success(request, 'Le compte a été ajouté avec succès.')
        return redirect('liste_admins')
    
    roles = Role.objects.all()
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/actions/creer_admin.html', {'entreprises': entreprises, 'roles': roles})


#Fonction pour retourner la vue vers la page de la liste des administrateurs
def liste_admins(request):
    # Vérifiez si l'utilisateur a le rôle 'Super admin'
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les administrateurs et leur compte associé
        admins = Admin.objects.select_related('compte').all()
        context = {
            'admins': admins,
        }
    else:
        # Si l'utilisateur n'est pas 'Super admin', afficher un message d'erreur
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page")
        return redirect('home_admin')
    
    # Rendre la page avec la liste des administrateurs
    return render(request, 'pages/admin/actions/liste_admins.html', context)

#Fonction pour la vue du profile
def profile_admin(request):
    user_id = request.session.get('user_id')
    # Vérification si l'utilisateur est connecté
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')
    user = get_object_or_404(Compte, id=user_id)
    # Vérification des droits d'accès à la page
    if not hasattr(user, 'role') or user.role.acce_page != "AD":
        messages.error(request, "Vous n'avez pas les droits d'accès à cette page.")
        return redirect('home_admin')

    # Récupération des informations administratives
    admin_info = Admin.objects.filter(compte=user).first()
    if not admin_info:
        messages.error(request, "Les informations administratives n'ont pas été trouvées.")
        return redirect('home_admin')

    # Mise à jour des informations de profil
    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        nom_admin = request.POST.get('nom_admin')
        prenom_admin = request.POST.get('prenom_admin')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')

        # Vérification de l'unicité de l'email et du téléphone
        if Compte.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec cet email existe déjà.")
        elif Compte.objects.filter(telephone=telephone).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec ce téléphone existe déjà.")
        else:
            # Mise à jour des informations du compte
            user.nom_utilisateur = nom_utilisateur
            user.email = email
            user.adresse = adresse
            user.telephone = telephone
            user.save()

            # Mise à jour des informations de l'administrateur
            admin_info.nom_admin = nom_admin
            admin_info.prenom_admin = prenom_admin
            admin_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_admin')

    return render(request, 'pages/admin/compte/profile.html', {'user': user, 'admin_info': admin_info})

# Fonction pour ajouter un salarié
def creer_salarie(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_utilisateur = generer_nom_utilisateur()
        email = request.POST.get('email')
        sexe = request.POST.get('sexe')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        role_id = request.POST.get('role')
        mot_de_passe = generer_mot_de_passe()
        
        nom_salarie = request.POST.get('nom_salarie')
        prenom_salarie = request.POST.get('prenom_salarie')
        dateNaissance = request.POST.get('dateNaissance')
        competences = request.POST.getlist('competences')
        departement_id = request.POST.get('departement')
        
        nom_identifiant_contrat = request.POST.get('nom_identifiant_contrat')
        type_contrat = request.POST.get('type_contrat')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        fonction_salarie = request.POST.get('fonction_salarie')
        detail = request.POST.get('detail')
        entreprise_id = request.POST.get('entreprise')

        errors = {}

        # Validation des données
        if not email:
            errors['email'] = "L'email est requis."
        elif Compte.objects.filter(email=email).exists():
            errors['email'] = "Un utilisateur avec cet email existe déjà."

        if not telephone:
            errors['telephone'] = "Le numéro de téléphone est requis."
        elif Compte.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Un utilisateur avec ce contact existe déjà."
            
        if not nom_identifiant_contrat:
            errors['nom_identifiant_contrat'] = "Le nom pour identifier le contrat est requis."
        elif Contrat.objects.filter(nom_identifiant_contrat=nom_identifiant_contrat).exists():
            errors['nom_identifiant_contrat'] = "Un contrat avec cet identifiant existe déjà."
        
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", nom_salarie):
            errors['nom_salarie'] = "Le nom du salarié ne peut contenir que des lettres."
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", prenom_salarie):
            errors['prenom_salarie'] = "Le prénom du salarié ne peut contenir que des lettres."

        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Vérification de l'existence des relations
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            errors['role'] = "Le rôle sélectionné n'existe pas."

        try:
            departement = Departement.objects.get(id=departement_id)
        except Departement.DoesNotExist:
            errors['departement'] = "Le département sélectionné n'existe pas."

        try:
            entreprise = Entreprise.objects.get(id=entreprise_id)
        except Entreprise.DoesNotExist:
            errors['entreprise'] = "L'entreprise sélectionnée n'existe pas."

        if errors:
            return render(request, 'pages/admin/salarie/creer_salarie.html', {
                'errors': errors,
                'email': email,
                'sexe': sexe,
                'adresse': adresse,
                'telephone': telephone,
                'role_id': role_id,
                'nom_salarie': nom_salarie,
                'prenom_salarie': prenom_salarie,
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'detail': detail,
                'departement_id': departement_id,
                'entreprise_id': entreprise_id,
                'fonction_salarie': fonction_salarie,
                'competences': competences,
                'roles': Role.objects.all(),
                'departements': Departement.objects.all(),
                'entreprises': Entreprise.objects.all(),
            })

        # Création du compte
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            sexe=sexe,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )

        # Création du salarié
        salarie = Salarie.objects.create(
            compte=compte,
            nom_salarie=nom_salarie,
            prenom_salarie=prenom_salarie,
            dateNaissance=dateNaissance,
            department_assigner=departement,
            creer_par=request.user
        )
        
        # Création du contrat
        contrat = Contrat.objects.create(
            nom_identifiant_contrat=nom_identifiant_contrat,
            type_contrat=type_contrat,
            salarie=salarie,
            date_debut=date_debut,
            date_fin=date_fin,
            fonction_salarie=fonction_salarie,
            detail=detail,
            entreprise=entreprise,
            creer_par=request.user
        )
        
        # Ajout des compétences
        for competence in competences:
            Competence.objects.create(salarie=salarie, competence=competence)

        # Envoi de l'email avec les identifiants de connexion
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        
        subject = "Bienvenue sur Stafflinker"
        message = f'''Bienvenue {nom_salarie} {prenom_salarie},

Votre compte a été créé.

Voici vos identifiants de connexion :

Nom d'utilisateur : {nom_utilisateur}
Mot de passe : {mot_de_passe}

Cordialement,
L'équipe Stafflinker'''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        if email:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
        else:
            # Logique d'envoi par WhatsApp (à implémenter)
            pass
        
        messages.success(request, 'Le compte a été ajouté avec succès.')
        return redirect('liste_salaries')
    
    roles = Role.objects.all()
    departements = Departement.objects.all()
    entreprises = Entreprise.objects.all()
    
    info_salarie = {
        'roles': roles,
        'departements': departements,
        'entreprises': entreprises,
    } 

    return render(request, 'pages/admin/salarie/creer_salarie.html', info_salarie)

def get_departements(request):
    entreprise_id = request.GET.get('entreprise_id')
    if entreprise_id:
        departements = Departement.objects.filter(entreprise_id=entreprise_id).values('id', 'nom_dep')
        return JsonResponse(list(departements), safe=False)
    return JsonResponse([], safe=False)

#Fonction pour voir le profil d'un salarié
def profile_salarie(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = get_object_or_404(Compte, id=user_id)

    if not hasattr(user, 'role') or user.role.acce_page != "SA":
        messages.error(request, "Vous n'avez pas les droits d'accès à cette page.")
        return redirect('home_salarie')

    try:
        salarie_info = Salarie.objects.get(compte=user)
    except Salarie.DoesNotExist:
        messages.error(request, "Les informations du salarié n'ont pas été trouvées.")
        return redirect('home_salarie')

    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        nom_salarie = request.POST.get('nom_salarie')
        prenom_salarie = request.POST.get('prenom_salarie')
        dateNaissance = request.POST.get('dateNaissance')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')

        # Vérification de l'unicité de l'email et du téléphone
        if Compte.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec cet email existe déjà.")
        elif Compte.objects.filter(telephone=telephone).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec ce téléphone existe déjà.")
        else:
            # Mise à jour des informations du compte
            user.nom_utilisateur = nom_utilisateur
            user.email = email
            user.adresse = adresse
            user.telephone = telephone
            user.save()

            # Mise à jour des informations du salarié
            salarie_info.nom_salarie = nom_salarie
            salarie_info.prenom_salarie = prenom_salarie
            salarie_info.dateNaissance = dateNaissance
            salarie_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_salarie')

    return render(request, 'pages/salarie/compte/profile.html', {'user': user, 'salarie_info': salarie_info})

#Fonction pour retourner la vue vers la page de la liste des salariés
def liste_salaries(request):
    # Vérifiez le rôle de l'utilisateur
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les clients, entreprises et salariés
        clients = Client.objects.select_related('compte', 'entreprise_affilier').all()
        entreprises = Entreprise.objects.all()
        salaries = Salarie.objects.select_related('compte', 'department_assigner', 'department_assigner__entreprise').all()
    else:
        # Filtrer les clients, entreprises et salariés par l'utilisateur qui les a créés
        clients = Client.objects.filter(creer_par=request.user).select_related('compte', 'entreprise_affilier')
        entreprises = Entreprise.objects.filter(creer_par=request.user)
        salaries = Salarie.objects.filter(creer_par=request.user).select_related('compte', 'department_assigner', 'department_assigner__entreprise')

    context = {
        'clients': clients,
        'salaries': salaries,
        'entreprises': entreprises
    }
    return render(request, 'pages/admin/salarie/liste_salaries.html', context)

#Fonction me permettant d'avoir tout les contrat en cours relations en avec un salarié
def liste_contrats_un_salarie(request, salarie_id):
    # Récupérer le salarié spécifique
    salarie = get_object_or_404(Salarie, id=salarie_id)

    # Vérifier les permissions
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les contrats (incluant les affectations) pour ce salarié
        contrats = Contrat.objects.filter(salarie=salarie).select_related('entreprise', 'salarie').prefetch_related(
            'affectation_set__entreprise_partenaire__entreprise',
            'affectation_set__client',
            'affectation_set__entreprise_simple'
        )
    else:
        contrats = Contrat.objects.filter(creer_par=request.user, salarie=salarie).select_related('entreprise', 'salarie').prefetch_related(
            'affectation_set__entreprise_partenaire__entreprise',
            'affectation_set__client',
            'affectation_set__entreprise_simple'
        )

    context = {
        'contrats': contrats,
        'salarie': salarie,
    }
    return render(request, 'pages/admin/salarie/liste_contrats_un_salarie.html', context)

def modifier_contrat_salarie(request, salarie_id, contrat_id):
    # Récupérer le salarié et le contrat spécifiques
    salarie = get_object_or_404(Salarie, id=salarie_id)
    contrat = get_object_or_404(Contrat, id=contrat_id, salarie=salarie)

    # Récupérer l'affectation s'il y en a une
    affectation = Affectation.objects.filter(contrat=contrat).first()
    
    if request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de modifier ce contrat.")
        return redirect('liste_contrats_un_salarie', salarie_id=salarie.id)

    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_identifiant_contrat = request.POST.get('nom_identifiant_contrat')
        type_contrat = request.POST.get('type_contrat')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        fonction_salarie = request.POST.get('fonction_salarie')
        entreprise_id = request.POST.get('entreprise')
        department_id = request.POST.get('department_assigner')
        detail = request.POST.get('detail')

        # Récupérer les données spécifiques à une affectation
        affectation_type = request.POST.get('affectationType')
        partenaire_id = request.POST.get('partenaire')
        client_id = request.POST.get('client')
        simple_id = request.POST.get('entreprise_simple')

        # Valider les données
        errors = {}
        if not nom_identifiant_contrat:
            errors['nom_identifiant_contrat'] = "L'identifiant du contrat est requis."
        elif Contrat.objects.filter(nom_identifiant_contrat=nom_identifiant_contrat).exclude(id=contrat_id).exists():
            errors['nom_identifiant_contrat'] = "Un contrat avec cet identifiant existe déjà."

        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."

        try:
            entreprise = Entreprise.objects.get(id=entreprise_id) if entreprise_id else None
        except Entreprise.DoesNotExist:
            errors['entreprise'] = "L'entreprise sélectionnée n'existe pas."

        try:
            departement = Departement.objects.get(id=department_id) if department_id else None
        except Departement.DoesNotExist:
            errors['department_assigner'] = "Le département sélectionné n'existe pas."

        if affectation_type == 'partenaire' and partenaire_id:
            try:
                partenaire = Partenaire.objects.get(id=partenaire_id)
            except Partenaire.DoesNotExist:
                errors['partenaire'] = "L'entreprise partenaire sélectionnée n'existe pas."
        elif affectation_type == 'client' and client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                errors['client'] = "Le client sélectionné n'existe pas."
        elif affectation_type == 'entreprise' and simple_id:
            try:
                entreprise_simple = Entreprise.objects.get(id=simple_id)
            except Entreprise.DoesNotExist:
                errors['entreprise_simple'] = "L'entreprise sélectionnée n'existe pas."

        if errors:
            return render(request, 'pages/admin/salarie/modifier_contrat_salarie.html', {
                'errors': errors,
                'contrat': contrat,
                'salarie': salarie,
                'entreprises': Entreprise.objects.all(),
                'departements': Departement.objects.all(),
                'partenaires': Partenaire.objects.all(),
                'clients': Client.objects.all(),
                'affectation': affectation,
            })

        # Mettre à jour le contrat
        contrat.nom_identifiant_contrat = nom_identifiant_contrat
        contrat.type_contrat = type_contrat
        contrat.date_debut = date_debut
        contrat.date_fin = date_fin
        contrat.fonction_salarie = fonction_salarie
        contrat.entreprise = entreprise
        contrat.detail = detail
        contrat.save()

        # Mettre à jour le département du salarié s'il s'agit d'un contrat simple
        if not affectation:
            salarie.department_assigner = departement
            salarie.save()

        # Mettre à jour l'affectation si elle existe
        if affectation:
            affectation.entreprise_partenaire = partenaire if affectation_type == 'partenaire' else None
            affectation.client = client if affectation_type == 'client' else None
            affectation.entreprise_simple = entreprise_simple if affectation_type == 'entreprise' else None
            affectation.save()

        messages.success(request, 'Les informations du contrat ont été mises à jour avec succès.')
        return redirect('liste_contrats_un_salarie', salarie_id=salarie.id)

    context = {
        'contrat': contrat,
        'salarie': salarie,
        'entreprises': Entreprise.objects.all(),
        'departements': Departement.objects.filter(entreprise=contrat.entreprise),
        'partenaires': Partenaire.objects.all(),
        'clients': Client.objects.all(),
        'affectation': affectation,
    }

    return render(request, 'pages/admin/salarie/modifier_contrat_salarie.html', context)

#Fonction pour terminer ou laissé un contrat en cours 
def statut_contrat_salarie(request, contrat_id):
    contrat_salarie = get_object_or_404(Contrat, id=contrat_id)
    contrat_salarie.est_terminer = not contrat_salarie.est_terminer
    contrat_salarie.save()
    messages.success(request, "Le statut du contrat du salarié a été mis à jour avec succès.")
    return redirect('liste_contrats_salaries')

#Fonction pour supprimer une compétence
def supprimer_competence(request, competence_id):
    # Récupérer la compétence à supprimer
    competence = get_object_or_404(Competence, id=competence_id)   
    # Supprimer la compétence
    competence.delete()

# Fonction pour retourner la vue vers la page de création de compte
def creer_entreprise(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        type_entreprise= request.POST.get('type_entreprise')
        nom_entreprise = request.POST.get('nom_entreprise')
        description = request.POST.get(' description ')
        site_web = request.POST.get('site_web') 
        
        # Valider les données
        errors = {}
        if Entreprise.objects.filter(nom_entreprise=nom_entreprise).exists():
            errors['nom_entreprise'] = "Une entreprise avec ce nom existe déjà."
        
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_client.html', {
                'errors': errors,
                'nom_entreprise': nom_entreprise,
                'entreprises': Entreprise.objects.all(),
            })
        Entreprise.objects.create(
            type_entreprise=type_entreprise,
            nom_entreprise=nom_entreprise,
            description=description,
            site_web=site_web,
            creer_par=request.user
        )
        
        messages.success(request, 'Entreprise ajouté avec succès.')
        return redirect('liste_entreprises')
    
    return render(request, 'pages/admin/entreprise/creer_entreprise.html')

def liste_entreprises(request):
    
    if request.user.role.acce_page == 'AD':
        entreprises = Entreprise.objects.all()
    else:
        entreprises = Entreprise.objects.filter(creer_par=request.user).select_related('creer_par')
        
    print(entreprises)
    return render(request, 'pages/admin/entreprise/liste_entreprises.html', {'entreprises': entreprises})

#Fonction pour modifier les informations d'une entreprise
def modifier_entreprise(request, entreprise_id):
    # Récupérer l'entreprise par son ID
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    
    # Vérifier si l'utilisateur a le droit de modifier cette entreprise
    if entreprise.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de modifier les informations de cette entreprise.")
        return redirect('liste_entreprises')

    if request.method == 'POST':
        # Récupération des données du formulaire
        type_entreprise = request.POST.get('type_entreprise')
        nom_entreprise = request.POST.get('nom_entreprise')
        description = request.POST.get('description')
        site_web = request.POST.get('site_web')

        # Validation des champs obligatoires
        errors = {}
        if not nom_entreprise:
            errors['nom_entreprise'] = "Le nom de l'entreprise est obligatoire."
        
        if errors:
            return render(request, 'pages/admin/entreprise/liste_entreprises.html', {
                'errors': errors,
                'entreprise': entreprise,
                'type_entreprise': type_entreprise,
                'nom_entreprise': nom_entreprise,
                'description': description,
                'site_web': site_web,
            })

        # Mise à jour des informations de l'entreprise
        entreprise.type_entreprise = type_entreprise
        entreprise.nom_entreprise = nom_entreprise
        entreprise.description = description
        entreprise.site_web = site_web
        entreprise.save()

        messages.success(request, "Les informations de l'entreprise ont été mises à jour avec succès.")
        return redirect('liste_entreprises')

    return render(request, 'pages/admin/entreprise/liste_entreprises.html', {
        'entreprise': entreprise,
        'type_entreprise': entreprise.type_entreprise,
        'nom_entreprise': entreprise.nom_entreprise,
        'description': entreprise.description,
        'site_web': entreprise.site_web,
    })

#Fonction pour supprimer une entreprise
def supprimer_entreprise(request, entreprise_id):
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    
    if entreprise.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de supprimer les informations de cette entreprise.")
        return redirect('liste_entreprises')

    # Vérifier s'il y a des départements avec des salariés liés à cette entreprise
    if Departement.objects.filter(entreprise=entreprise, salarie__isnull=False).exists():
        messages.error(request, "Impossible de supprimer cette entreprise car elle a des départements avec des salariés associés.")
        return redirect('liste_entreprises')

    # Suppression partielle : marquer l'entreprise comme inactive
    entreprise.est_active = False
    entreprise.save()

    messages.success(request, "L'entreprise a été désactivée avec succès.")
    return redirect('liste_entreprises')


    # Rediriger vers la liste des entreprises après suppression
    return redirect('liste_entreprises')

# Fonction pour retourner la vue vers la page de création de compte
def creer_partenaire(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_utilisateur = generer_nom_utilisateur()
        sexe = request.POST.get('sexe')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        role_id = request.POST.get('role')
        mot_de_passe = generer_mot_de_passe()
        
        nom_agent_entreprise = request.POST.get('nom_agent_entreprise')
        prenom_agent_entreprise = request.POST.get('prenom_agent_entreprise')
        poste_agent = request.POST.get('poste_agent')
        entreprise_id = request.POST.get('entreprise')
        
        # Valider les données
        errors = {}
        if Compte.objects.filter(email=email).exists():
            errors['email'] = "Un utilisateur avec cet email existe déjà."
        if Compte.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Un utilisateur avec ce contact existe déjà."
        
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            errors['role'] = "Rôle invalide."
        try:
            entreprise = Entreprise.objects.get(id=entreprise_id, type_entreprise="Entreprise partenaire")
        except Entreprise.DoesNotExist:
            errors['entreprise'] = "Entreprise invalide ou non éligible."
        
        if errors:
            return render(request, 'pages/admin/partenaires/creer_partenaire.html', {
                'errors': errors,
                'email': email,
                'role': role ,
                'telephone': telephone,
                'nom_agent_entreprise': nom_agent_entreprise,
                'prenom_agent_entreprise': prenom_agent_entreprise,
                'entreprise': entreprise,
                'roles': Role.objects.all(),
                'entreprises': Entreprise.objects.filter(type_entreprise="Entreprise partenaire"),
            })
        
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            sexe=sexe,
            email=email,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )
        
        Partenaire.objects.create(
            compte=compte,
            nom_agent_entreprise=nom_agent_entreprise,
            prenom_agent_entreprise=prenom_agent_entreprise,
            poste_agent=poste_agent,
            entreprise=entreprise,
            creer_par=request.user
        )
        
        # Charger les paramètres d'email
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        
        # Envoyer l'email avec les identifiants de connexion
        subject = "Bienvenue sur HrBridge",
        message = f'''Nous souhaitons la bienvenue à votre entreprise,

Le compte de votre entreprise à été créer avec pour représentant M/Mme {nom_agent_entreprise} {prenom_agent_entreprise}

Voici vos identifiants de connexion.

Nom d'utilisateur: {nom_utilisateur}
Mot de passe: {mot_de_passe}

Cordialement,
L'équipe'''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        if email:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
        else:
            # Logique d'envoi par WhatsApp (à implémenter)
            pass
        
        messages.success(request, 'Le compte a été ajouté avec succès.')
        return redirect('liste_partenaires')
    
    roles = Role.objects.all()
    entreprises = Entreprise.objects.filter(type_entreprise="Entreprise partenaire")
    
    context = {
        'roles': roles,
        'entreprises': entreprises
    } 
    
    return render(request, 'pages/admin/partenaires/creer_partenaire.html', context)

#Fonction pour retourner la vue vers la page de la liste des entreprises
def liste_partenaires(request):
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les entreprises et salariés
        entreprises = Partenaire.objects.all()
        salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()
    else:
        # Filtrer les clients, entreprises et salariés par l'utilisateur qui les a créés
        entreprises = Partenaire.objects.filter(creer_par=request.user)
        salaries = Salarie.objects.filter(creer_par=request.user).select_related('compte').prefetch_related('competence_set')

    context = {
        'salaries': salaries,
        'entreprises': entreprises
    }

    return render(request, 'pages/admin/partenaires/liste_partenaires.html', context)

#Fonction profile entreprise
def profile_partenaire(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = get_object_or_404(Compte, id=user_id)

    if not hasattr(user, 'role') or user.role.acce_page != "EN":
        messages.error(request, "Vous n'avez pas les droits d'accès à cette page.")
        return redirect('home_partenaire')

    try:
        partenaire_info = Partenaire.objects.select_related('entreprise').get(compte=user)
        entreprise_info = partenaire_info.entreprise
    except Partenaire.DoesNotExist:
        messages.error(request, "Les informations de l'entreprise partenaire n'ont pas été trouvées.")
        return redirect('home_partenaire')

    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        nom_entreprise = request.POST.get('nom_entreprise')
        nom_agent_entreprise = request.POST.get('nom_agent_entreprise')
        prenom_agent_entreprise = request.POST.get('prenom_agent_entreprise')
        poste_agent = request.POST.get('poste_agent')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        site_web = request.POST.get('site_web')
        description = request.POST.get('description')

        if Compte.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec cet email existe déjà.")
        elif Compte.objects.filter(telephone=telephone).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec ce téléphone existe déjà.")
        else:
            user.nom_utilisateur = nom_utilisateur
            user.email = email
            user.adresse = adresse
            user.telephone = telephone
            user.save()

            entreprise_info.nom_entreprise = nom_entreprise
            entreprise_info.site_web = site_web
            entreprise_info.description = description
            entreprise_info.save()

            partenaire_info.nom_agent_entreprise = nom_agent_entreprise
            partenaire_info.prenom_agent_entreprise = prenom_agent_entreprise
            partenaire_info.poste_agent = poste_agent
            partenaire_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_partenaire')

    return render(request, 'pages/partenaires/compte/profile.html', {
        'user': user, 
        'entreprise_info': entreprise_info, 
        'partenaire_info': partenaire_info
    })

# Fonction pour retourner la vue vers la page de création de compte
def creer_client(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_utilisateur = generer_nom_utilisateur()
        email = request.POST.get('email')
        sexe = request.POST.get('sexe')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        role_id = request.POST.get('role')
        mot_de_passe = generer_mot_de_passe()
        
        type_client= request.POST.get('type_client')
        nom_client = request.POST.get('nom_client')
        prenom_client = request.POST.get('prenom_client')
        entreprise_id = request.POST.get('entreprise')

        # Valider les données
        errors = {}
        if Compte.objects.filter(email=email).exists():
            errors['email'] = "Un utilisateur avec cet email existe déjà."
        if Compte.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Un utilisateur avec ce contact existe déjà."
        # Validation des champs nom et prénom
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", nom_client):
            errors['nom_client'] = "Le nom du client ne peut contenir que des lettres."
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", prenom_client):
            errors['prenom_client'] = "Le prénom du client ne peut contenir que des lettres."
        
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            errors['role'] = "Rôle invalide."
        
        entreprise_affilier = None
        if entreprise_id:
            try:
                entreprise_affilier = Entreprise.objects.get(id=entreprise_id)
            except Entreprise.DoesNotExist:
                errors['entreprise'] = "Entreprise invalide."
        
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_client.html', {
                'errors': errors,
                'email': email,
                'sexe': sexe,
                'adresse': adresse,
                'telephone': telephone,
                'role_id': role_id,
                'nom_client': nom_client,
                'prenom_client': prenom_client,
                'entreprise_id': entreprise_id,
                'roles': Role.objects.all(),
                'entreprises': Entreprise.objects.all()
            })
        
        # Créer le compte
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            sexe=sexe,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )

        # Créer le modèle Client associé
        Client.objects.create(
            compte=compte,
            type_client=type_client,
            nom_client=nom_client,
            prenom_client=prenom_client,
            entreprise_affilier=entreprise_affilier,
            creer_par=request.user
        )
        
        # Charger les paramètres d'email
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']

        # Envoyer l'email avec les identifiants de connexion
        subject = "Bienvenue sur HrBridge"
        message = f'''Nous souhaitons la bienvenue à {nom_client} {prenom_client},

Votre compte a été créé.

Voici vos identifiants de connexion.

Nom d'utilisateur: {nom_utilisateur}
Mot de passe: {mot_de_passe}

Cordialement,
L'équipe'''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]

        if email:
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
        else:
            # Logique d'envoi par WhatsApp (à implémenter)
            pass

        messages.success(request, 'Le compte a été ajouté avec succès.')
        return redirect('liste_clients')
    
    roles = Role.objects.all()
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/clients/creer_client.html', {'entreprises': entreprises, 'roles': roles})

#Fonction pour retourner la vue vers la page de la liste des entreprises
def liste_clients(request):
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les clients, entreprises et salariés
        clients = Client.objects.select_related('compte', 'entreprise_affilier').all()
        entreprises = Entreprise.objects.all()
        salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()
    else:
        # Filtrer les clients, entreprises et salariés par l'utilisateur qui les a créés
        clients = Client.objects.filter(creer_par=request.user).select_related('compte', 'entreprise_affilier')
        entreprises = Entreprise.objects.filter(creer_par=request.user)
        salaries = Salarie.objects.filter(creer_par=request.user).select_related('compte').prefetch_related('competence_set')

    context = {
        'clients': clients,
        'salaries': salaries,
        'entreprises': entreprises
    }
    return render(request,'pages/admin/clients/liste_clients.html',context)

#Fonction vers la vue du profile du client
def profile_client(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = get_object_or_404(Compte, id=user_id)

    if not hasattr(user, 'role') or user.role.acce_page != 'CL':
        messages.error(request, "Vous n'avez pas les droits d'accès à cette page.")
        return redirect('home_client')

    try:
        client_info = Client.objects.get(compte=user)
    except Client.DoesNotExist:
        messages.error(request, "Les informations du client n'ont pas été trouvées.")
        return redirect('home_client')

    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        nom_client = request.POST.get('nom_client')
        prenom_client = request.POST.get('prenom_client')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        entreprise_affilier = request.POST.get('entreprise_affilier')

        if Compte.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec cet email existe déjà.")
        elif Compte.objects.filter(telephone=telephone).exclude(id=user.id).exists():
            messages.error(request, "Un utilisateur avec ce téléphone existe déjà.")
        else:
            user.nom_utilisateur = nom_utilisateur
            user.email = email
            user.adresse = adresse
            user.telephone = telephone
            user.save()

            client_info.nom_client = nom_client
            client_info.prenom_client = prenom_client
            client_info.entreprise_affilier = entreprise_affilier
            client_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_client')

    return render(request, 'pages/client/compte/profile.html', {'user': user, 'client_info': client_info})

#Fonction pour activé ou désactivé un compte
def statut(request, user_id):
    compte = Compte.objects.get(id=user_id)
    compte.is_active = not compte.is_active
    compte.save()
    messages.success(request, f"Le statut de {compte.nom_utilisateur} a été mis à jour.")
    # Redirection basée sur l'accès de l'utilisateur
    if compte.role.acce_page == "AD":
        return redirect('liste_admins')
    elif compte.role.acce_page == "SA":
        return redirect('liste_salaries')
    elif compte.role.acce_page == "EN":
        return redirect('liste_partenaires')
    elif compte.role.acce_page == "CL":
        return redirect('liste_clients')
    if compte.role.acce_page == "GE":
        return redirect('liste_admins')
    else:
        return redirect('home_admin')

#Fonction pour éffectuer une affectation
def affecter_salarie(request, salarie_id):
    # Récupérer le salarié à affecter
    salarie = get_object_or_404(Salarie, id=salarie_id)
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        partenaire_id = request.POST.get('entreprise_partenaire')
        client_id = request.POST.get('client')
        simple_id= request.POST.get('entreprise_simple')
        
        nom_identifiant_contrat = request.POST.get('nom_identifiant_contrat')
        type_contrat = request.POST.get('type_contrat')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        fonction_salarie = request.POST.get('fonction_salarie')
        entreprise_id = request.POST.get('entreprise')
        
        # Valider les données
        errors = {}
        
        # Validation du nom d'identifiant de contrat
        if not nom_identifiant_contrat:
            errors['nom_identifiant_contrat'] = "Le nom pour identifier le contrat est requis."
        elif Contrat.objects.filter(nom_identifiant_contrat=nom_identifiant_contrat).exists():
            errors['nom_identifiant_contrat'] = "Un contrat avec cet identifiant existe déjà."
        
        # Validation de l'affectation (soit un partenaire, un client ou une entreprise simple doit être sélectionné)
        if not partenaire_id and not client_id and not simple_id:
            errors['affectation'] = "Vous devez sélectionner soit une entreprise partenaire, soit un client, soit une entreprise."
        elif sum([bool(partenaire_id), bool(client_id), bool(simple_id)]) > 1:
            errors['affectation'] = "Vous ne pouvez sélectionner qu'une seule option parmi entreprise partenaire, client ou entreprise simple."

        # Validation des dates
        if date_debut and date_fin:
            if date_debut > date_fin:
                errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
            if date_fin < date_debut:
                errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Vérification de l'existence des objets sélectionnés
        entreprise_partenaire = None
        client = None
        entreprise_simple = None
        entreprise = None

        try:
            entreprise_partenaire = Partenaire.objects.get(id=partenaire_id) if partenaire_id else None
        except Partenaire.DoesNotExist:
            errors['entreprise_partenaire'] = "L'entreprise partenaire sélectionnée n'existe pas."

        try:
            client = Client.objects.get(id=client_id) if client_id else None
        except Client.DoesNotExist:
            errors['client'] = "Le client sélectionné n'existe pas."

        try:
            entreprise_simple = Entreprise.objects.get(id=simple_id) if simple_id else None
        except Entreprise.DoesNotExist:
            errors['entreprise_simple'] = "L'entreprise sélectionnée n'existe pas."

        try:
            entreprise = Entreprise.objects.get(id=entreprise_id) if entreprise_id else None
        except Entreprise.DoesNotExist:
            errors['entreprise'] = "L'entreprise sélectionnée n'existe pas."
        
        if errors:
            return render(request, 'pages/admin/affectations/affecter_salarie.html', {
                'errors': errors,
                'nom_identifiant_contrat': nom_identifiant_contrat,
                'type_contrat': type_contrat,
                'date_debut': date_debut,
                'date_fin': date_fin,
                'fonction_salarie': fonction_salarie,
                'entreprise_partenaire': partenaire_id,
                'client': client_id,
                'entreprise_simple': simple_id,
                'salarie': salarie,
                'partenaires': Partenaire.objects.all(),
                'entreprises': Entreprise.objects.all(),
                'entreprise_simple': Entreprise.objects.filter(partenaire__isnull=True),
                'clients': Client.objects.all(),
            })
        
        # Création du contrat
        contrat = Contrat.objects.create(
            nom_identifiant_contrat=nom_identifiant_contrat,
            salarie=salarie,
            entreprise=entreprise,
            date_debut=date_debut,
            date_fin=date_fin,
            fonction_salarie=fonction_salarie,
            type_contrat=type_contrat,
            creer_par=request.user
        )
        
        # Créer l'affectation
        affectation = Affectation.objects.create(
            contrat=contrat,
            entreprise_partenaire=entreprise_partenaire,
            client=client,
            entreprise_simple=entreprise_simple,
            creer_par=request.user
        )

        # Envoi des emails de notification
        emails_to_send = []
        if entreprise_partenaire:
            emails_to_send.append(entreprise_partenaire.compte.email)
        if client:
            emails_to_send.append(client.compte.email)
        if entreprise_simple:
            emails_to_send.append(entreprise_simple.creer_par.email)
        
        # Email du salarié
        if salarie.compte.email:
            emails_to_send.append(salarie.compte.email)
        
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        # Envoyer les emails
        if emails_to_send:
            send_mail(
                subject="Nouvelle Affectation",
                message=f"Bonjour,\n\nUne nouvelle affectation a été effectuée pour {salarie.nom_salarie} {salarie.prenom_salarie}. Veuillez vérifier les détails de l'affectation.",
                from_email = settings.EMAIL_HOST_USER,
                recipient_list=emails_to_send,
                fail_silently=False,
            )
        
        messages.success(request, 'Le salarié a été affecté avec succès et les emails ont été envoyés.')
        return redirect('liste_contrats_affectations')
    
    # Charger les partenaires et clients pour le formulaire
    partenaires = Partenaire.objects.all()
    clients = Client.objects.all()
    entreprises = Entreprise.objects.all()
    entreprise_simple = Entreprise.objects.filter(partenaire__isnull=True)
    
    return render(request, 'pages/admin/affectations/affecter_salarie.html', {
        'salarie': salarie,
        'partenaires': partenaires,
        'entreprises': entreprises,
        'entreprise_simple': entreprise_simple,
        'clients': clients,
    }) 

#Fonction pour modifier une affection
def modifier_affectation(request, affectation_id):
    # Récupérer l'affectation spécifique
    affectation = get_object_or_404(Affectation, id=affectation_id)
    
    # Vérifier si l'utilisateur a le droit de modifier cette affectation
    if affectation.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de modifier les informations de cette affectation.")
        return redirect('liste_contrats_affectations')
    
    contrat = affectation.contrat
    salarie = contrat.salarie  # Récupérer le salarié associé au contrat

    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_identifiant_contrat = request.POST.get('nom_identifiant_contrat')
        type_contrat = request.POST.get('type_contrat')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        fonction_salarie = request.POST.get('fonction_salarie')
        detail= request.POST.get('detail')
        entreprise_id = request.POST.get('entreprise')
        salarie_id = request.POST.get('salarie')  # Nouveau : pour changer le salarié associé

        affectation_type = request.POST.get('affectationType')
        partenaire_id = request.POST.get('partenaire')
        client_id = request.POST.get('client')
        simple_id = request.POST.get('entreprise_simple')

        # Valider les données
        errors = {}

        # Validation des champs du contrat
        if not nom_identifiant_contrat:
            errors['nom_identifiant_contrat'] = "Le nom pour identifier le contrat est requis."
        elif Contrat.objects.filter(nom_identifiant_contrat=nom_identifiant_contrat).exclude(id=contrat.id).exists():
            errors['nom_identifiant_contrat'] = "Un contrat avec cet identifiant existe déjà."

        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."

        # Validation des entités pour l'affectation
        if affectation_type == 'partenaire' and partenaire_id:
            try:
                partenaire = Partenaire.objects.get(id=partenaire_id)
            except Partenaire.DoesNotExist:
                errors['partenaire'] = "L'entreprise partenaire sélectionnée n'existe pas."
        elif affectation_type == 'client' and client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                errors['client'] = "Le client sélectionné n'existe pas."
        elif affectation_type == 'entreprise' and simple_id:
            try:
                entreprise_simple = Entreprise.objects.get(id=simple_id)
            except Entreprise.DoesNotExist:
                errors['entreprise_simple'] = "L'entreprise sélectionnée n'existe pas."

        # Validation du salarié
        try:
            salarie = Salarie.objects.get(id=salarie_id) if salarie_id else salarie
        except Salarie.DoesNotExist:
            errors['salarie'] = "Le salarié sélectionné n'existe pas."

        # Gérer les erreurs
        if errors:
            return render(request, 'pages/admin/affectations/modifier_affectation.html', {
                'errors': errors,
                'contrat': contrat,
                'affectation': affectation,
                'entreprises': Entreprise.objects.all(),
                'partenaires': Partenaire.objects.all(),
                'clients': Client.objects.all(),
                'salaries': Salarie.objects.all(),  # Passer la liste des salariés
                'entreprise_simple': Entreprise.objects.filter(partenaire__isnull=True),
            })

        # Mettre à jour le contrat
        contrat.nom_identifiant_contrat = nom_identifiant_contrat
        contrat.type_contrat = type_contrat
        contrat.date_debut = date_debut
        contrat.date_fin = date_fin
        contrat.fonction_salarie = fonction_salarie
        contrat.entreprise_id = entreprise_id
        contrat.detail = detail
        contrat.salarie = salarie  # Mettre à jour le salarié associé
        contrat.save()

        # Mettre à jour l'affectation
        affectation.entreprise_partenaire = partenaire if affectation_type == 'partenaire' else None
        affectation.client = client if affectation_type == 'client' else None
        affectation.entreprise_simple = entreprise_simple if affectation_type == 'entreprise' else None
        affectation.save()

        messages.success(request, "Mis à jour effectué avec succès.")
        return redirect('liste_contrats_affectations')

    context = {
        'contrat': contrat,
        'affectation': affectation,
        'entreprises': Entreprise.objects.all(),
        'partenaires': Partenaire.objects.all(),
        'clients': Client.objects.all(),
        'salaries': Salarie.objects.all(),  # Passer la liste des salariés pour les options du formulaire
        'entreprise_simple': Entreprise.objects.filter(partenaire__isnull=True),
    }

    return render(request, 'pages/admin/affectations/modifier_affectation.html', context)
 
# Récupérer tous les contrats liés aux affectations
def liste_contrats_affectations(request):
    # Vérifiez le rôle de l'utilisateur
    if request.user.role.acce_page == 'AD':
        # Super admin peut voir toutes les affectations
        affectations = Affectation.objects.select_related('contrat', 'entreprise_partenaire', 'entreprise_simple', 'client').all()
    else:
        # Autres utilisateurs ne voient que leurs affectations
        affectations = Affectation.objects.filter(creer_par=request.user).select_related('contrat', 'entreprise_partenaire', 'entreprise_simple', 'client').all()

    context = {
        'affectations': affectations,
    }

    return render(request, 'pages/admin/affectations/liste_contrats_affectations.html', context)

#Pour supprimer une affectation
def supprimer_affectation(request, affectation_id):
    # Récupérer l'affectation à supprimer
    affectation = get_object_or_404(Affectation, id=affectation_id)

    # Vérifier si l'utilisateur a le droit de supprimer cette affectation
    if affectation.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de supprimer cette affectation.")
        return redirect('liste_contrats_affectations')

    # Vérifier si le contrat lié à l'affectation est terminé
    if not affectation.contrat.est_terminer:
        messages.error(request, "Vous ne pouvez pas supprimer cette affectation car le contrat associé n'est pas encore terminé.")
        return redirect('liste_contrats_affectations')

    # Supprimer l'affectation (ce qui entraîne la suppression en cascade des objets liés)
    affectation.delete()

    # Message de succès
    messages.success(request, "L'affectation et toutes les entités liées ont été supprimées avec succès.")

    # Rediriger vers la liste des affectations après suppression
    return redirect('liste_contrats_affectations')

#Fonction pour terminer ou laissé un contrat en cours 
def statut_contrat_affectation(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)
    contrat.est_terminer = not contrat.est_terminer
    contrat.save()
    messages.success(request, "Le statut du contrat lié à l'affectation a été mis à jour avec succès.")
    return redirect('liste_contrats_affectations')

#Fonction pour éditer un contrat
def editer_doc_contrat(request, contrat_id):
    # Récupérer le contrat spécifique
    contrat = get_object_or_404(Contrat, id=contrat_id)
    doc_contrat = Doc_contrat.objects.filter(contrat=contrat).first()
    
    if  request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission d'éditer ce contrat'.")
        return redirect('liste_doc_contrats')

    if request.method == 'POST':
        # Récupérer les données du formulaire
        titre_contrat = request.POST.get('titre_contrat')
        soustitre_contrat = request.POST.get('soustitre_contrat')
        text_intro_contrat = request.POST.get('text_intro_contrat')
        article_titres = request.POST.getlist('article_titres')
        article_details = request.POST.getlist('article_details')

        # Valider les données
        errors = {}
        if not titre_contrat:
            errors['titre_contrat'] = "Le titre du contrat est requis."
        if not article_titres or not article_details:
            errors['articles'] = "Au moins un article est requis."

        if errors:
            return render(request, 'pages/admin/doc_contrats/editer_doc_contrat.html', {
                'errors': errors,
                'doc_contrat': doc_contrat,
                'contrat': contrat,
            })

        # Enregistrer ou mettre à jour le Doc_contrat
        if not doc_contrat:
            doc_contrat = Doc_contrat.objects.create(
                contrat=contrat,
                titre_contrat=titre_contrat,
                soustitre_contrat=soustitre_contrat,
                text_intro_contrat=text_intro_contrat,
                creer_par=request.user
            )
        else:
            doc_contrat.titre_contrat = titre_contrat
            doc_contrat.soustitre_contrat = soustitre_contrat
            doc_contrat.text_intro_contrat = text_intro_contrat
            doc_contrat.save()

        # Supprimer les articles existants
        Article.objects.filter(doc_contrat=doc_contrat).delete()

        # Créer les nouveaux articles
        for titre, detail in zip(article_titres, article_details):
            if titre.strip() and detail.strip():
                Article.objects.create(
                    doc_contrat=doc_contrat,
                    titre_article=titre,
                    detail_article=detail
                )

        messages.success(request, "Edition effectuer avec succès.")
        return redirect('editer_doc_contrat', contrat_id=contrat.id)
    
    articles = Article.objects.filter(doc_contrat=doc_contrat)

    return render(request, 'pages/admin/doc_contrats/editer_doc_contrat.html', {
        'doc_contrat': doc_contrat,
        'contrat': contrat,
        'articles': articles,
    })

#Fonction pour retourner la vue vers la page de la liste des contrats
def liste_doc_contrats(request):
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les documents de contrat, excluant ceux liés aux affectations
        doc_contrats = Doc_contrat.objects.all()
        pdfs = EnregistrerPDF.objects.filter(fiche_de_paie_affectation__isnull=True)
    else:
        doc_contrats = Doc_contrat.objects.filter(creer_par=request.user)
        pdfs = EnregistrerPDF.objects.filter(creer_par=request.user, fiche_de_paie_affectation__isnull=True)

    # Passer les documents au contexte pour les afficher dans la vue
    context = {
        'doc_contrats': doc_contrats,
        'pdfs': pdfs
    }
    return render(request, 'pages/admin/doc_contrats/liste_doc_contrats.html', context)


# Détail d'un document de contrat
def detail_contrat(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)
    doc_contrat = Doc_contrat.objects.filter(contrat=contrat).first()
    articles = Article.objects.filter(doc_contrat=doc_contrat)

    context = {
        'contrat': contrat,
        'doc_contrat': doc_contrat,
        'articles': articles,
    }

    return render(request, 'pages/admin/doc_contrats/editer_doc_contrat.html', context)

#Vue pour éditer une fiche de paie
def editer_fichePaie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)

    if request.method == 'POST' and 'next' in request.POST:
        # Récupération des données du formulaire
        periode = request.POST.get('periode')
        detail = request.POST.get('detail')
        salaire_base = float(request.POST.get('salaire_base', 0))
        jour_non_travailler = int(request.POST.get('jour_non_travailler', 0))
        taux_journalier = float(request.POST.get('taux_journalier', 0))
        heures_supp = int(request.POST.get('heures_supp', 0))
        taux_heure_supp = float(request.POST.get('taux_heure_supp', 0))
        nbre_jour_travail = int(request.POST.get('nbre_jour_travail', 0))
        prime_ancien = float(request.POST.get('prime_ancien', 0))
        prime_salissure = float(request.POST.get('prime_salissure', 0))
        prime_panier = float(request.POST.get('prime_panier', 0))
        indemnite_depl = float(request.POST.get('indemnite_depl', 0))
        retenue_css = float(request.POST.get('retenue_css', 0))
        retenue_amu = float(request.POST.get('retenue_amu', 0))

        # Validation des champs pour s'assurer qu'ils ne sont pas négatifs
        errors = {}
        if salaire_base < 0:
            errors['salaire_base'] = "Le salaire de base ne peut pas être négatif."
        if jour_non_travailler < 0:
            errors['jour_non_travailler'] = "Le nombre de jours non travaillés ne peut pas être négatif."
        if taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if heures_supp < 0:
            errors['heures_supp'] = "Le nombre d'heures supplémentaires ne peut pas être négatif."
        if taux_heure_supp < 0:
            errors['taux_heure_supp'] = "Le taux pour les heures supplémentaires ne peut pas être négatif."
        if nbre_jour_travail < 0:
            errors['nbre_jour_travail'] = "Le nombre de jours travaillés ne peut pas être négatif."
        if prime_ancien < 0:
            errors['prime_ancien'] = "La prime d'ancienneté ne peut pas être négative."
        if prime_salissure < 0:
            errors['prime_salissure'] = "La prime de salissure ne peut pas être négative."
        if prime_panier < 0:
            errors['prime_panier'] = "La prime panier ne peut pas être négative."
        if indemnite_depl < 0:
            errors['indemnite_depl'] = "L'indemnité de déplacement ne peut pas être négative."
        if retenue_css < 0:
            errors['retenue_css'] = "La retenue CSS ne peut pas être négative."
        if retenue_amu < 0:
            errors['retenue_amu'] = "La retenue AMU ne peut pas être négative."

        if errors:
            return render(request, 'pages/admin/fiches_paie/editer_fichePaie.html', {
                'errors': errors,
                'salarie': salarie
            })

        # Si tout est valide, afficher le récapitulatif
        context = {
            'periode': periode,
            'detail': detail,
            'salaire_base': salaire_base,
            'jour_non_travailler': jour_non_travailler,
            'taux_journalier': taux_journalier,
            'heures_supp': heures_supp,
            'taux_heure_supp': taux_heure_supp,
            'nbre_jour_travail': nbre_jour_travail,
            'prime_ancien': prime_ancien,
            'prime_salissure': prime_salissure,
            'prime_panier': prime_panier,
            'indemnite_depl': indemnite_depl,
            'retenue_css': retenue_css,
            'retenue_amu': retenue_amu,
            'salarie': salarie
        }
        return render(request, 'pages/admin/fiches_paie/editer_fichePaie.html', context)

    return render(request, 'pages/admin/fiches_paie/editer_fichePaie.html', {
        'salarie': salarie
    })

#Valider l'édition d'une fiche de paie
def valider_fichePaie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)

    if request.method == 'POST' and 'valider' in request.POST:
        salaire_base = float(request.POST.get('salaire_base', 0))
        jour_non_travailler = int(request.POST.get('jour_non_travailler', 0))
        taux_journalier = float(request.POST.get('taux_journalier', 0))
        heures_supp = int(request.POST.get('heures_supp', 0))
        taux_heure_supp = float(request.POST.get('taux_heure_supp', 0))
        nbre_jour_travail = int(request.POST.get('nbre_jour_travail', 0))
        prime_ancien = float(request.POST.get('prime_ancien', 0))
        prime_salissure = float(request.POST.get('prime_salissure', 0))
        prime_panier = float(request.POST.get('prime_panier', 0))
        indemnite_depl = float(request.POST.get('indemnite_depl', 0))
        retenue_css = float(request.POST.get('retenue_css', 0))
        retenue_amu = float(request.POST.get('retenue_amu', 0))

        # Calcul du salaire mensuel
        salaire_mensuel = salaire_base + (nbre_jour_travail * taux_journalier) + (heures_supp * taux_heure_supp) - (jour_non_travailler * taux_journalier)
        salaire_net = salaire_mensuel + prime_ancien + prime_salissure + prime_panier + indemnite_depl - retenue_css - retenue_amu

        # Création de la fiche de paie
        FicheDePaieSalarie.objects.create(
            salarie=salarie,
            salaire_base=salaire_base,
            jour_non_travailler=jour_non_travailler,
            taux_journalier=taux_journalier,
            salaire_mensuel=salaire_mensuel,
            heure_supp=heures_supp,
            taux_heure_supp=taux_heure_supp,
            nbre_jour_travail=nbre_jour_travail,
            prime_ancien=prime_ancien,
            prime_salissure=prime_salissure,
            prime_panier=prime_panier,
            indemnite_depl=indemnite_depl,
            retenue_css=retenue_css,
            retenue_amu=retenue_amu,
            salaire_net=salaire_net,
            creer_par=request.user
        )

        messages.success(request, f'Fiche de paie pour {salarie.nom_salarie} créée avec succès.')
        return redirect('liste_fichesPaie')

    return redirect('editer_fichePaie', salarie_id=salarie.id)

def liste_fiches_de_paie_salarie(request, salarie_id):
    # Récupérer le salarié par son ID
    salarie = get_object_or_404(Salarie, id=salarie_id)

    # Vérifier les permissions
    if request.user.role.acce_page == 'AD':  # Vérifiez le rôle de l'utilisateur
        # Récupérer les fiches de paie payées et impayées
        fiches_paie_payees = FicheDePaieSalarie.objects.filter(salarie=salarie, est_payer=True)
        fiches_paie_impayees = FicheDePaieSalarie.objects.filter(salarie=salarie, est_payer=False)
    else:
        fiches_paie_payees = FicheDePaieSalarie.objects.filter(creer_par=request.user, salarie=salarie, est_payer=True)
        fiches_paie_impayees = FicheDePaieSalarie.objects.filter(creer_par=request.user, salarie=salarie, est_payer=False)

    context = {
        'salarie': salarie,
        'fiches_paie_payees': fiches_paie_payees,
        'fiches_paie_impayees': fiches_paie_impayees,
    }
    return render(request, 'pages/admin/fiches_paie/liste_fiches_de_paie_salarie.html', context)

#Fonction pour retourner la vue vers la page de la liste des fiches de paies
def liste_fichesPaie(request):
    if request.user.role.acce_page == 'AD':  # Vérifiez le rôle de l'utilisateur
        fiches_de_paie = FicheDePaieSalarie.objects.all()
    else:
        fiches_de_paie = FicheDePaieSalarie.objects.filter(creer_par=request.user)

    return render(request,'pages/admin/fiches_paie/liste_fichesPaie.html', {'fiches_de_paie': fiches_de_paie})

def statut_fichePaie(request, fiche_id):
    fiche_salarie = FicheDePaieSalarie.objects.get(id=fiche_id)
    fiche_salarie.est_payer = not fiche_salarie.est_payer  # Inverser le statut de paiement
    fiche_salarie.save()
    messages.success(request, "Le statut de paiement a été mis à jour.")
    return redirect('liste_fichesPaie')

#Edition d'une fiche de paie lié à une affectation
def editer_fichePaie_affectation(request, affectation_id):
    # Récupérer l'affectation spécifique
    affectation = get_object_or_404(Affectation, id=affectation_id)
    contrat = affectation.contrat  # Obtenir le contrat associé
    fiche_de_paie = FicheDePaieAffectation.objects.filter(affectation=affectation).first()

    # Vérifier les permissions (si nécessaire)
    if contrat.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de créer cette fiche de paie.")
        return redirect('liste_affectations')

    if request.method == 'POST':
        # Récupérer les données soumises par l'utilisateur
        nom_identifiant_paie_affectation = request.POST.get('nom_identifiant_paie_affectation')
        echeance = request.POST.get('echeance')
        detail = request.POST.get('detail')
        heure_travail = request.POST.get('heure_travail')
        taux_heure_travail = request.POST.get('taux_heure_travail')
        heure_supp = request.POST.get('heure_supp')
        taux_heure_supp = request.POST.get('taux_heure_supp')
        nbre_jour_travail = request.POST.get('nbre_jour_travail')
        prime_salissure = request.POST.get('prime_salissure')
        indemnite_depl = request.POST.get('indemnite_depl')
        est_payer = request.POST.get('est_payer', False) == 'on'

        # Validation pour s'assurer que le montant n'est pas négatif
        errors = {}
            
        try:
            heure_travail = float(heure_travail.replace(',', '.')) if heure_travail else 0
        except ValueError:
            errors['heure_travail'] = "Le nombre d'heures de travail doit être un nombre valide."
            
        try:
            taux_heure_travail = float(taux_heure_travail.replace(',', '.')) if taux_heure_travail else 0
        except ValueError:
            errors['taux_heure_travail'] = "Le taux horaire doit être un nombre valide."
            
        try:
            heure_supp = float(heure_supp.replace(',', '.')) if heure_supp else 0
        except ValueError:
            errors['heure_supp'] = "Le nombre d'heures supplémentaires doit être un nombre valide."
    
        try:
            taux_heure_supp = float(taux_heure_supp.replace(',', '.')) if taux_heure_supp else 0
        except ValueError:
            errors['taux_heure_supp'] = "Le taux pour les heures supplémentaires doit être un nombre valide."
            
        try:
            nbre_jour_travail = float(nbre_jour_travail.replace(',', '.')) if nbre_jour_travail else 0
        except ValueError:
            errors['nbre_jour_travail'] = "Le nombre de jours travaillés doit être un nombre valide."
        try:
            prime_salissure = float(prime_salissure.replace(',', '.')) if prime_salissure else 0
        except ValueError:
            errors['prime_salissure'] = "La prime de salissure doit être un nombre valide."
        try:
            indemnite_depl = float(indemnite_depl.replace(',', '.')) if indemnite_depl else 0
        except ValueError:
            errors['indemnite_depl'] = "L'indemnité de déplacement doit être un nombre valide."
        
        if heure_travail < 0:
            errors['heure_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if taux_heure_travail < 0:
            errors['taux_heure_travail'] = "Le taux pour les heures de travail ne peut pas être négatif."
        if heure_supp < 0:
            errors['heure_supp'] = "Le nombre d'heures supplémentaires ne peut pas être négatif."
        if taux_heure_supp < 0:
            errors['taux_heure_supp'] = "Le taux pour les heures supplémentaires ne peut pas être négatif."
        if nbre_jour_travail < 0:
            errors['nbre_jour_travail'] = "Le nombre de jours travaillés ne peut pas être négatif."
        if prime_salissure < 0:
            errors['prime_salissure'] = "La prime de salissure ne peut pas être négative."
        if indemnite_depl < 0:
            errors['indemnite_depl'] = "L'indemnité de déplacement ne peut pas être négative."

        if errors:
            return render(request, 'pages/admin/fiches_paie/editer_fichePaie_affectation_form.html', {
                'errors': errors,
                'fiche_de_paie': fiche_de_paie,
                'affectation': affectation,
            })
        
        # Calcul du montant de base et du montant total
        montant_de_base = nbre_jour_travail * (heure_travail * taux_heure_travail + heure_supp * taux_heure_supp)
        montant_total = montant_de_base + prime_salissure + indemnite_depl

        # Mettre à jour ou créer une nouvelle fiche de paie
        if fiche_de_paie:
            fiche_de_paie.nom_identifiant_paie_affectation = nom_identifiant_paie_affectation
            fiche_de_paie.echeance = echeance
            fiche_de_paie.heure_travail = heure_travail
            fiche_de_paie.taux_heure_travail = taux_heure_travail
            fiche_de_paie.heure_supp = heure_supp
            fiche_de_paie.taux_heure_supp = taux_heure_supp
            fiche_de_paie.nbre_jour_travail = nbre_jour_travail
            fiche_de_paie.prime_salissure = prime_salissure
            fiche_de_paie.indemnite_depl = indemnite_depl
            fiche_de_paie.montant_de_base = montant_de_base
            fiche_de_paie.montant_total = montant_total
            fiche_de_paie.est_payer = est_payer
            fiche_de_paie.detail = detail
            fiche_de_paie.save()
        else:
            FicheDePaieAffectation.objects.create(
                nom_identifiant_paie_affectation=nom_identifiant_paie_affectation,
                echeance=echeance,
                heure_travail=heure_travail,
                taux_heure_travail=taux_heure_travail,
                heure_supp=heure_supp,
                taux_heure_supp=taux_heure_supp,
                nbre_jour_travail=nbre_jour_travail,
                prime_salissure=prime_salissure,
                indemnite_depl=indemnite_depl,
                montant_de_base=montant_de_base,
                montant_total=montant_total,
                est_payer=est_payer,
                detail=detail,
                affectation=affectation,
                creer_par=request.user
            )

        messages.success(request, "Fiche de paie éditée avec succès.")
        return redirect('detail_fiche_de_paie_affectation', affectation_id=affectation.id)  # Rediriger vers une page de votre choix

    return render(request, 'pages/admin/fiches_paie/editer_fichePaie_affectation_form.html', {
        'affectation': affectation,
        'contrat': contrat,
        'fiche_de_paie': fiche_de_paie,
    })
    
def detail_fiche_de_paie_affectation(request, affectation_id):
    # Récupérer l'affectation spécifique
    affectation = get_object_or_404(Affectation, id=affectation_id)
    fiche_de_paie = FicheDePaieAffectation.objects.filter(affectation=affectation).first()

    # Vérifier les permissions (si nécessaire)
    if affectation.creer_par != request.user and request.user.role.acce_page != 'AD':
        messages.error(request, "Vous n'avez pas la permission de voir cette fiche de paie.")
        return redirect('liste_fichesPaie_affectation')

    context = {
        'affectation': affectation,
        'fiche_de_paie': fiche_de_paie,
    }
    return render(request, 'pages/admin/fiches_paie/editer_fichePaie_affectation.html', context)

def liste_fichesPaie_affectation(request):
    if request.user.role.acce_page == 'AD':
        # Récupérer tous les PDFs liés aux fiches de paie affectation
        fiches_de_paie_affectation = FicheDePaieAffectation.objects.all()
        pdfs = EnregistrerPDF.objects.filter(fiche_de_paie_affectation__isnull=False)
    else:
        pdfs = EnregistrerPDF.objects.filter(creer_par=request.user, fiche_de_paie_affectation__isnull=False)
        fiches_de_paie_affectation = FicheDePaieAffectation.objects.filter(creer_par=request.user)

    # Passer les documents au contexte pour les afficher dans la vue
    context = {
        'pdfs': pdfs,
        'fiches_de_paie_affectation': fiches_de_paie_affectation
    }

    return render(request, 'pages/admin/fiches_paie/liste_fichesPaie_affectation.html', context)

def statut_fichePaie_affectation(request, fiche_id):
    fiche_affectation = FicheDePaieAffectation.objects.get(id=fiche_id)
    fiche_affectation.est_payer = not fiche_affectation.est_payer  # Inverser le statut de paiement
    fiche_affectation.save()
    messages.success(request, "Le statut de paiement a été mis à jour.")
    return redirect('liste_fichesPaie_affection')

def configurer_email(request):
    email_settings = EmailSettings.objects.first()
    if request.method == 'POST':
        email_settings.host = request.POST['host']
        email_settings.port = request.POST['port']
        email_settings.use_tls = 'use_tls' in request.POST
        email_settings.use_ssl = 'use_ssl' in request.POST
        email_settings.host_user = request.POST['host_user']
        email_settings.host_password = request.POST['host_password']
        email_settings.save()
        messages.success(request, 'Les paramètres d\'email ont été mis à jour avec succès.')
        return redirect('configurer_email')

    return render(request, 'pages/admin/setting/email.html', {'email_settings': email_settings})

#Fonction pour faire demande salarié
def demande_salarie(request):
    if request.method == 'POST':
        # Récupération des données du formulaire
        titre = request.POST.get('titre')
        details = request.POST.get('details')

        # Validation des champs obligatoires
        errors = {}
        if not titre:
            errors['titre'] = "Le champ titre est obligatoire."
        if not details:
            errors['details'] = "Le champ détails est obligatoire."

        if errors:
            return render(request, 'pages/admin/pages/creer/creer_demande_salarie.html', {
                'errors': errors,
                'titre': titre,
                'details': details,
            })

        # Création de la demande de salarié
        Demande.objects.create(
            compte=request.user,
            titre=titre,
            details=details,
        )

        messages.success(request, "La demande de salarié a été créée avec succès.")
        return redirect('liste_demandes_salarie')

    return render(request, 'pages/admin/demandes/demande_salarie.html')

def demande_client(request):
    if request.method == 'POST':
        # Récupération des données du formulaire
        titre = request.POST.get('titre')
        details = request.POST.get('details')

        # Validation des champs obligatoires
        errors = {}
        if not titre:
            errors['titre'] = "Le champ titre est obligatoire."
        if not details:
            errors['details'] = "Le champ détails est obligatoire."

        if errors:
            return render(request, 'pages/client/actions/demande.html', {
                'errors': errors,
                'titre': titre,
                'details': details,
            })

        # Création de la demande de salarié
        Demande.objects.create(
            compte=request.user,
            titre=titre,
            details=details,
        )

        messages.success(request, "Demande effectuer avec succès.")
        return redirect('mes_demandes_client')

    return render(request, 'pages/client/actions/demande.html')

def mes_demandes_client(request):
    # Vérifier que l'utilisateur est connecté
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    # Récupérer les demandes créées par l'utilisateur connecté
    demandes = Demande.objects.filter(compte=request.user).order_by('-fait_le')

    context = {
        'demandes': demandes,
    }
    return render(request, 'pages/client/actions/mes_demandes.html', context)

def demande_partenaire(request):
    if request.method == 'POST':
        # Récupération des données du formulaire
        titre = request.POST.get('titre')
        details = request.POST.get('details')

        # Validation des champs obligatoires
        errors = {}
        if not titre:
            errors['titre'] = "Le champ titre est obligatoire."
        if not details:
            errors['details'] = "Le champ détails est obligatoire."

        if errors:
            return render(request, 'pages/partenaire/actions/demande.html', {
                'errors': errors,
                'titre': titre,
                'details': details,
            })

        # Création de la demande de salarié
        Demande.objects.create(
            compte=request.user,
            titre=titre,
            details=details,
        )

        messages.success(request, "Demande effectuer avec succès.")
        return redirect('mes_demandes_partenaire')

    return render(request, 'pages/partenaire/actions/demande.html')

def mes_demandes_partenaire(request):
    # Vérifier que l'utilisateur est connecté
    if not request.user.is_authenticated:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    # Récupérer les demandes créées par l'utilisateur connecté
    demandes = Demande.objects.filter(compte=request.user).order_by('-fait_le')

    context = {
        'demandes': demandes,
    }
    return render(request, 'pages/partenaire/actions/mes_demandes.html', context)

#Fonction pour afficher liste demande salarié en attente
def liste_demandes(request):
    if request.user.role.acce_page in ['AD', 'GE']:  # Exemples de rôles autorisés
        demandes = Demande.objects.All().order_by('-fait_le')
    else:
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('home_admin')
    context = {
        'demandes': demandes,
    }

    return render(request, 'pages/admin/demandes/liste_demandes.html', context)

#Changer statut demande
def changer_statut_demande(request, demande_id):
    demande = get_object_or_404(Demande, id=demande_id)

    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')

        if nouveau_statut in ['VALIDE', 'REFUSE']:
            demande.statut = nouveau_statut
            demande.save()
            messages.success(request, "Le statut de la demande a été mis à jour.")

    return redirect('liste_demandes')

#fonction pour charger et appliquer dynamiquement les paramètres d'email à partir de la base de données.
def load_email_settings():
    email_settings = EmailSettings.objects.first()
    if email_settings:
        return {
            'EMAIL_HOST': email_settings.host,
            'EMAIL_PORT': email_settings.port,
            'EMAIL_USE_TLS': email_settings.use_tls,
            'EMAIL_USE_SSL': email_settings.use_ssl,
            'EMAIL_HOST_USER': email_settings.host_user,
            'EMAIL_HOST_PASSWORD': email_settings.host_password,
        }
    return None

#Partie pdf
def envoyer_contrat_pdf (request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)
    doc_contrat = get_object_or_404(Doc_contrat, contrat=contrat)
    articles = Article.objects.filter(doc_contrat=doc_contrat)

    context = {
        'contrat': contrat,
        'doc_contrat': doc_contrat,
        'articles': articles,
        'date': datetime.datetime.today()  # Ajout de la date dans le contexte
    }
    
    # Charger le template
    template = get_template('pages/admin/pdf/contrat.html')
    html = template.render(context)
    
    # Options du format PDF
    options = {
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        "enable-local-file-access": "",
        'debug-javascript': True
    }

    
    # Générer le PDF
    pdf = pdfkit.from_string(html, False, options)
    
    pdf_name = f"{contrat.nom_identifiant_contrat}.pdf"
    pdf_path = os.path.join('pdfs', pdf_name)
    stored_pdf = EnregistrerPDF(contrat=contrat)
    
    pdf_file = BytesIO(pdf)
    stored_pdf.file.save(pdf_name, File(pdf_file), save=True)
    
    # Envoyer le PDF par email
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f"attachment; filename={contrat.nom_identifiant_contrat}.pdf"
    
    if pdf:
        # Charger les paramètres d'email
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
            
        subject = f"Contrat {contrat.nom_identifiant_contrat}"
        message = f"Voici le contrat après affectation du salarié { contrat.salarie.nom_salarie} {contrat.salarie.prenom_salarie}"
        f"Veuillez trouver ci-joint votre contrat de travail."
        
        email_recipients = [contrat.salarie.compte.email]  # Commencez par ajouter l'email du salarié

        # Ajouter l'email de l'employeur en fonction du type d'employeur dans le contrat
        if contrat.affectation_set.exists():
            affectation = contrat.affectation_set.first()
            if affectation.client:
                email_recipients.append(affectation.client.compte.email)
            elif affectation.entreprise_partenaire:
                email_recipients.append(affectation.entreprise_partenaire.entreprise.compte.email)
            elif affectation.entreprise_simple:
                email_recipients.append(affectation.entreprise_simple.creer_par.email)
        else:
            if contrat.entreprise:
                email_recipients.append(None)

        # Envoyer l'email à tous les destinataires
        email = EmailMessage(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            email_recipients
        )

        # Ajouter le PDF en pièce jointe
        email.attach(f"{contrat.nom_identifiant_contrat}.pdf", pdf, 'application/pdf')

        # Envoyer l'email
        email.send()
    
    return response

def envoyer_contrat_pdf_paie_affectation(request, affectation_id):
    affectation = get_object_or_404(Affectation, id=affectation_id)
    fiche_de_paie = FicheDePaieAffectation.objects.filter(affectation=affectation).first()

    context = {
        'affectation': affectation,
        'fiche_de_paie': fiche_de_paie,
        'date': datetime.datetime.today()  # Ajout de la date dans le contexte
    }

    # Charger le template
    template = get_template('pages/admin/pdf/fiche_de_paie_affectation.html')
    html = template.render(context)

    # Options du format PDF
    options = {
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        "enable-local-file-access": "",
        'debug-javascript': True
    }

    # Générer le PDF
    pdf = pdfkit.from_string(html, False, options)

    # Nommer et stocker le PDF
    pdf_name = f"{fiche_de_paie.nom_identifiant_paie_affectation}.pdf"
    pdf_path = os.path.join('pdfs', pdf_name)
    stored_pdf = EnregistrerPDF(fiche_de_paie_affectation=fiche_de_paie)  # Associez correctement à la fiche de paie

    pdf_file = BytesIO(pdf)
    stored_pdf.file.save(pdf_name, File(pdf_file), save=True)

    # Préparer la réponse HTTP pour le téléchargement du PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f"attachment; filename={fiche_de_paie.nom_identifiant_paie_affectation}.pdf"

    # Envoi par email
    if pdf:
        # Charger les paramètres d'email
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']

        subject = f"Fiche de paie {fiche_de_paie.nom_identifiant_paie_affectation}"
        message = (f"Voici la fiche de paie du contrat {affectation.contrat.nom_identifiant_contrat} "
                   f"qui s'est déroulé du {affectation.contrat.date_debut} au {affectation.contrat.date_fin} "
                   f"avec le salarié {affectation.contrat.salarie.nom_salarie} {affectation.contrat.salarie.prenom_salarie}. "
                   "Veuillez trouver ci-joint votre fiche de paie.")

        # Liste des destinataires en fonction de l'affectation
        email_recipients = []

        if affectation.client:
            email_recipients.append(affectation.client.compte.email)
        elif affectation.entreprise_partenaire:
            email_recipients.append(affectation.entreprise_partenaire.entreprise.compte.email)
        elif affectation.entreprise_simple:
            email_recipients.append(affectation.entreprise_simple.creer_par.email)

        # Envoyer l'email
        email = EmailMessage(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            email_recipients
        )

        # Ajouter le PDF en pièce jointe
        email.attach(pdf_name, pdf, 'application/pdf')

        # Envoyer l'email
        email.send()

    return response
