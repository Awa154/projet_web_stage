import re
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.utils import timezone
from datetime import date, datetime
from django.template.loader import get_template
from .models import Clause, Client, Competence, Compte, Contrat, EmailSettings, Entreprise,Admin, Departement, FicheDePaie, Role, Salarie, calculer_montant_final
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
import random, string, datetime
from django.db.models import Q, Count
import pdfkit
config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

# Create your views here.

#Fonction pour retourner la vue vers la page d'accueil de l'admin
def home(request):
    return render(request,'pages/home/home.html')

#Fonction pour retourner la vue vers la page d'accueil de l'admin
def home_admin(request):
    salaries = Compte.objects.select_related('role').filter(role__nom_role="Salarié")
    entreprises = Compte.objects.select_related('role').filter(role__nom_role="Entreprise partenaire")
    clients = Compte.objects.select_related('role').filter(role__nom_role="Client")
    contrats=Contrat.objects.all()
    
    # Statistiques
    total_salaries =salaries.count()
    total_partners = entreprises.count()
    total_clients=clients.count()
    total_contrats=contrats.count()
    context = {
        'total_contrats': total_contrats,
        'total_salaries': total_salaries,
        'total_partners':total_partners,
        'total_clients':total_clients,
    }
    return render(request,'pages/admin/pages/dashboard/home.html', context)

#Fonction pour retourner la vue vers la page d'accueil
def home_salarie(request):
    return render(request,'pages/salarie/dashboard/home.html')

#Fonction pour retourner la vue vers la page d'accueil
def home_entreprise(request):
    return render(request,'pages/entreprise/dashboard/home.html')

#Fonction pour retourner la vue vers la page d'accueil
def home_client(request):
    return render(request,'pages/client/dashboard/home.html')

#Fonction pour retourner la vue vers la page d'accueil
def home_test(request):
    return render(request,'pages/admin/pages/dashboard/test.html')

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
                return redirect('home_entreprise')
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
        return render(request, "pages/auth/pages/login.html")
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
            
    return render(request, "pages/auth/pages/forget_password.html")

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

    return render(request, 'pages/auth/pages/change_password.html')

#Création de la vue pour créer un département
def creer_departement(request):
    if request.method == 'POST':
        nom_dep = request.POST['nom_dep']
        try:
            departement = Departement.objects.create(nom_dep=nom_dep, creer_par=request.user)
            messages.success(request, 'Département créé avec succès.')
            return redirect('liste_departements')
        except IntegrityError:
            messages.error(request, 'Un département avec ce nom existe déjà.')
            
    return render(request, 'pages/admin/pages/creer/creer_departement.html')

#Fonction pour afficher la liste des départements
def liste_departements(request):
    if request.user.role.nom_role == 'Super admin':  # Vérifiez le rôle de l'utilisateur
        departements = Departement.objects.annotate(nombre_salaries=Count('salarie'))
    else:
        departements = Departement.objects.filter(creer_par=request.user).annotate(nombre_salaries=Count('salarie'))
    
    return render(request, 'pages/admin/pages/liste/liste_departement.html', {'departements': departements})

#Fonction pour modifier un département
def modifier_departement(request, departement_id):
    departement = get_object_or_404(Departement, id=departement_id)

    # Vérifier si l'utilisateur a le droit de modifier ce département
    if departement.creer_par != request.user and request.user.role.nom_role != 'Super admin':
        messages.error(request, "Vous n'avez pas la permission de modifier ce département.")
        return redirect('liste_departements')

    if request.method == 'POST':
        nom_dep = request.POST.get('nom_dep')

        # Vérifier si un département avec ce nom existe déjà
        if Departement.objects.filter(nom_dep=nom_dep).exclude(id=departement_id).exists():
            messages.error(request, 'Un département avec ce nom existe déjà.')
            return redirect('modifier_departement', departement_id=departement_id)  
            
        departement.nom_dep = nom_dep
        departement.save()
        messages.success(request, 'Le département a été mis à jour avec succès.')
        return redirect('liste_departements')  # Rediriger vers la liste des départements après modification

    return render(request, 'pages/admin/pages/modifier/modifier_departement.html', {
        'departement': departement
    })

#Supprimer un département
def supprimer_departement(request, departement_id):
    departement = get_object_or_404(Departement, id=departement_id)

    # Vérifier si l'utilisateur a le droit de supprimer ce département
    if departement.creer_par != request.user and request.user.role.nom_role != 'Super admin':
        messages.error(request, "Vous n'avez pas la permission de supprimer ce département.")
        return redirect('liste_departements')

    # Vérifier si le département contient des salariés
    if Salarie.objects.filter(departement=departement).exists():
        messages.error(request, "Impossible de supprimer ce département car il contient des salariés.")
        return redirect('liste_departements')  # Redirigez vers la liste des départements ou une autre page appropriée

    departement.delete()
    messages.success(request, "Le département a été supprimé avec succès.")
    return redirect('liste_departements')

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
            return redirect('liste_role')
        except IntegrityError:
            messages.error(request, 'Un rôle avec ce nom existe déjà.')

    return render(request, 'pages/admin/pages/creer/creer_role.html')

#Fonction pour retourner la vue vers la page de la liste des salariés
def liste_role(request):
    roles = Role.objects.all()

    context = {
        'roles': roles,
    }
    return render(request,'pages/admin/pages/liste/liste_role.html', context)

# Modifier un rôle
def modifier_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)

    if request.method == 'POST':
        nom_role = request.POST.get('nom_role')
        acce_page = request.POST.get('acce_page')
        
        # Vérifier si un rôle avec ce nom existe déjà
        if Role.objects.filter(nom_role=nom_role).exclude(id=role_id).exists():
            messages.error(request, 'Un rôle avec ce nom existe déjà.')
            return redirect('liste_role')
            
        role.nom_role = nom_role
        role.acce_page = acce_page
        role.save()
        
        messages.success(request, 'Le rôle a été mis à jour avec succès.')
        return redirect('liste_role') # Rediriger vers la liste des rôles après modification

    return render(request, 'pages/admin/pages/liste/liste_role.html', {'role': role})

#supprimer un rôle
def supprimer_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    
    if Compte.objects.filter(role=role).exists():
        messages.error(request, "Impossible de supprimer ce rôle car il contient des comptes associés.")
        return redirect('liste_role')  # Redirigez vers la liste des rôles ou une autre page appropriée
    
    role.delete()
    messages.success(request, "Le rôle a été supprimé avec succès.")
    return redirect('liste_role')

#Fonction pour créer un administrateur
def creer_admin(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_utilisateur = generer_nom_utilisateur()
        email = request.POST['email']
        sexe = request.POST['sexe']
        adresse = request.POST['adresse']
        telephone = request.POST['telephone']
        role_id = request.POST['role']
        role = Role.objects.get(id=role_id)
        mot_de_passe = generer_mot_de_passe()
        
        nom_admin = request.POST['nom_admin']
        prenom_admin = request.POST['prenom_admin']
        fonction_admin = request.POST['fonction_admin']
        
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
                'departements': Departement.objects.all(),
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
        
        Admin.objects.create(
            compte=compte,
            nom_admin=nom_admin,
            prenom_admin=prenom_admin,
            fonction_admin=fonction_admin,
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
        message = f'''Bienvenue {nom_admin} {prenom_admin},

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
        return redirect('liste_admin')
    
    roles = Role.objects.all()
    departements = Departement.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_admin.html', {'departements': departements, 'roles': roles})

#Fonction pour retourner la vue vers la page de la liste des administrateurs
def liste_admin(request):
    if request.user.role.nom_role == 'Super admin':  # Vérifiez le rôle de l'utilisateur
        admins = Admin.objects.select_related('compte').all()
        context = {
            'admins': admins,
        }
    else:
        messages.error(request, "Vous n'avez pas la permission d'accéder à cette page")
        return redirect('liste_departements')
    
    return render(request, 'pages/admin/pages/liste/liste_admin.html', context)

#Fonction pour la vue du profile
def profile_admin(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = get_object_or_404(Compte, id=user_id)

    if not hasattr(user, 'role') or user.role.acce_page != "AD":
        messages.error(request, "Vous n'avez pas les droits d'accès à cette page.")
        return redirect('home_admin')

    try:
        admin_info = Admin.objects.get(compte=user)
    except Admin.DoesNotExist:
        messages.error(request, "Les informations administratives n'ont pas été trouvées.")
        return redirect('home_admin')

    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        nom_admin = request.POST.get('nom_admin')
        prenom_admin = request.POST.get('prenom_admin')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')

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

            admin_info.nom_admin = nom_admin
            admin_info.prenom_admin = prenom_admin
            admin_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_admin')
        
    return render(request, 'pages/admin/pages/dashboard/profile.html', {'user': user, 'admin_info': admin_info})

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
        annee_exp = request.POST.get('annee_exp')
        departement_id = request.POST.get('departement')
        entreprise_id = request.POST.get('entreprise')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        type_contrat = request.POST.get('type_contrat')
        fonction_salarie = request.POST.get('fonction_salarie')
        mode_paiement = request.POST.get('mode_paiement')
        taux_horaire = request.POST.get('taux_horaire')
        heures_travail = request.POST.get('heures_travail')
        jours_travail = request.POST.get('jours_travail')
        taux_journalier = request.POST.get('taux_journalier')
        salaire_mensuel = request.POST.get('salaire_mensuel')
        competences = request.POST.getlist('competences')
        clauses = request.POST.getlist('clauses')

        errors = {}
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        try:
            taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        except ValueError:
            errors['taux_horaire'] = "Le taux horaire doit être un nombre valide."
        try:
            heures_travail = int(heures_travail) if heures_travail else 0
        except ValueError:
            errors['heures_travail'] = "Le nombre d'heures de travail doit être un nombre entier."
        try:
            jours_travail = int(jours_travail) if jours_travail else 0
        except ValueError:
            errors['jours_travail'] = "Le nombre de jours de travail doit être un nombre entier."
        try:
            taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        except ValueError:
            errors['taux_journalier'] = "Le taux journalier doit être un nombre valide."
        try:
            salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        except ValueError:
            errors['salaire_mensuel'] = "Le salaire mensuel doit être un nombre valide."
        
        # Vérifier l'unicité de l'email et du contact
        if Compte.objects.filter(email=email).exists():
            errors['email'] = "Un utilisateur avec cet email existe déjà."
        if Compte.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Un utilisateur avec ce contact existe déjà."
        
        # Validation des champs nom et prénom
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", nom_salarie):
            errors['nom_salarie'] = "Le nom du salarié ne peut contenir que des lettres."
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", prenom_salarie):
            errors['prenom_salarie'] = "Le prénom du salarié ne peut contenir que des lettres."

        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Validation des valeurs négatives
        if annee_exp and int(annee_exp) < 0:
            errors['annee_exp'] = "Le nombre d'années d'expérience ne peut pas être négatif."
        if taux_horaire is not 0 and taux_horaire < 0:
            errors['taux_horaire'] = "Le taux horaire ne peut pas être négatif."
        if heures_travail is not 0 and heures_travail < 0:
            errors['heures_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if jours_travail is not 0 and jours_travail < 0:
            errors['jours_travail'] = "Le nombre de jours de travail ne peut pas être négatif."
        if taux_journalier is not 0 and taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if salaire_mensuel is not 0 and salaire_mensuel < 0:
            errors['salaire_mensuel'] = "Le salaire mensuel ne peut pas être négatif."
            
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_salarie.html', {
                'errors': errors,
                'email': email,
                'sexe': sexe,
                'adresse': adresse,
                'telephone': telephone,
                'role_id': role_id,
                'nom_salarie': nom_salarie,
                'prenom_salarie': prenom_salarie,
                'annee_exp': annee_exp, 
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'fonction_salarie': fonction_salarie,
                'mode_paiement': mode_paiement,
                'taux_horaire': taux_horaire,
                'heures_travail': heures_travail,
                'jours_travail': jours_travail,
                'taux_journalier': taux_journalier,
                'salaire_mensuel': salaire_mensuel,
                'entreprise_id': entreprise_id,
                'departement_id': departement_id,
                'clauses':clauses,
                'competences':competences,
                'roles': Role.objects.all(),
                'departements': Departement.objects.all(),
                'entreprises': Entreprise.objects.all(),
            })
        
        role = Role.objects.get(id=role_id)
        departement = Departement.objects.get(id=departement_id)
        entreprise = Entreprise.objects.get(id=entreprise_id)
        
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            sexe=sexe,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )

        salarie = Salarie.objects.create(
            compte=compte,
            nom_salarie=nom_salarie,
            prenom_salarie=prenom_salarie,
            dateNaissance=dateNaissance,
            annee_exp=annee_exp,
            departement=departement,
            creer_par=request.user
        )

        for competence in competences:
            Competence.objects.create(salarie=salarie, competence=competence)

        contrat = Contrat.objects.create(
            salarie=salarie,
            entreprise=entreprise,
            date_debut=date_debut,
            date_fin=date_fin,
            type_contrat=type_contrat,
            fonction_salarie=fonction_salarie,
            mode_paiement=mode_paiement,
            taux_horaire=taux_horaire,
            heures_travail=heures_travail,
            jours_travail=jours_travail,
            taux_journalier=taux_journalier,
            salaire_mensuel=salaire_mensuel,
            creer_par=request.user
        )
        
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)
        
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        
        subject = "Bienvenue sur HrBridge"
        message = f'''Bienvenue {nom_salarie} {prenom_salarie},

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
        return redirect('liste_salarie')
    
    roles = Role.objects.all()
    departements = Departement.objects.all()
    entreprises = Entreprise.objects.all()
    
    info_salarie = {
        'roles': roles,
        'departements': departements,
        'entreprises': entreprises,
    } 

    return render(request, 'pages/admin/pages/creer/creer_salarie.html', info_salarie)

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
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')

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

            salarie_info.nom_salarie = nom_salarie
            salarie_info.prenom_salarie = prenom_salarie
            salarie_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_salarie')

    return render(request, 'pages/salarie/dashboard/profile.html', {'user': user, 'salarie_info': salarie_info})

#Fonction pour retourner la vue vers la page de la liste des salariés
def liste_salarie(request):
    if request.user.role.nom_role == 'Super admin':  # Vérifiez le rôle de l'utilisateur
        clients = Client.objects.select_related('compte').all()
        entreprises = Entreprise.objects.select_related('compte').all()
        salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()
    else:
        clients = Client.objects.filter(creer_par=request.user).select_related('compte')
        entreprises = Entreprise.objects.filter(creer_par=request.user).select_related('compte')
        salaries = Salarie.objects.filter(creer_par=request.user).select_related('compte').prefetch_related('competence_set')

    context = {
        'clients': clients,
        'salaries': salaries,
        'entreprises': entreprises
    }
    return render(request, 'pages/admin/pages/liste/liste_salarie.html', context)


# Modifier un salarié
def modifier_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    
    # Vérifier si l'utilisateur a le droit de modifier ce salarié
    if salarie.creer_par != request.user and request.user.role.nom_role != 'Super admin':
        messages.error(request, "Vous n'avez pas la permission de modifier les informations de ce salarié.")
        return redirect('liste_salarie')
    
    if request.method == 'POST':
        nom_salarie = request.POST.get('nom_salarie')
        prenom_salarie = request.POST.get('prenom_salarie')
        annee_exp = request.POST.get('annee_exp')
        departement_id = request.POST.get('departement')
        
        competences = request.POST.getlist('competences')
        for competence in competences:
            Competence.objects.create(salarie=salarie, competence=competence)
        
        salarie.nom_salarie = nom_salarie
        salarie.prenom_salarie = prenom_salarie
        salarie.annee_exp = annee_exp
        salarie.departement_id = departement_id
        salarie.save()
        
        # Gestion des competences
        existing_competences = request.POST.getlist('competences')
        
        # Supprimer toutes les competences existantes
        salarie.competence_set.all().delete()
        
        # Ajouter les nouvelles competences
        for competence_text in existing_competences:
            if competence_text.strip():
                new_competence = Competence(salarie=salarie, competence=competence_text)
                new_competence.save()
        
        messages.success(request, 'Les informations du salarié a été mis à jour avec succès.')
        return redirect('liste_salarie') # Rediriger vers la liste des salaries après modification

    return render(request, 'pages/admin/pages/liste/liste_salarie.html', {'salarie': salarie})

# Fonction pour retourner la vue vers la page de création de compte
def creer_partenaire(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom_utilisateur = generer_nom_utilisateur()
        email = request.POST['email']
        adresse = request.POST['adresse']
        telephone = request.POST['telephone']
        role_id = request.POST['role']
        role = Role.objects.get(id=role_id)
        mot_de_passe = generer_mot_de_passe()
        # Créer le modèle associé basé sur le rôle de l'utilisateur
        nom_entreprise = request.POST.get('nom_entreprise')
        nom_agent_entreprise = request.POST.get('nom_agent_entreprise ')
        prenom_agent_entreprise = request.POST.get('prenom_agent_entreprise ')
        poste_agent = request.POST.get('poste_agent')
        secteur_activite = request.POST.get('secteur_activite')
        site_web = request.POST.get('site_web')
        
        # Valider les données
        errors = {}
        if Compte.objects.filter(email=email).exists():
            errors['email'] = "Un utilisateur avec cet email existe déjà."
        if Compte.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Un utilisateur avec ce contact existe déjà."
        if Entreprise.objects.filter(nom_entreprise=nom_entreprise).exists():
            errors['nom_entreprise'] = "Une entreprise avec ce nom existe déjà."
        # Validation des champs nom et prénom
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", nom_agent_entreprise):
            errors['nom_agent_entreprise'] = "Le nom de l'agent ne peut contenir que des lettres."
        if not re.match("^[a-zA-ZÀ-ÿ ]*$", prenom_agent_entreprise):
            errors['prenom_agent_entreprise'] = "Le prénom de l'agent ne peut contenir que des lettres."
        
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            errors['role'] = "Rôle invalide."
        
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_client.html', {
                'errors': errors,
                'email': email,
                'adresse': adresse,
                'telephone': telephone,
                'role_id': role_id,
                'nom_entreprise': nom_entreprise,
                'nom_agent_entreprise': nom_agent_entreprise,
                'prenom_agent_entreprise': prenom_agent_entreprise,
                'poste_agent': poste_agent,
                'roles': Role.objects.all(),
            })
        
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )
        
        Entreprise.objects.create(
            compte=compte,
            nom_entreprise=nom_entreprise,
            nom_agent_entreprise=nom_agent_entreprise,
            poste_agent=poste_agent,
            prenom_agent_entreprise =prenom_agent_entreprise ,
            secteurActivite=secteur_activite,
            site_web=site_web,
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
        message = f'''Nous souhaitons la bienvenue à {nom_entreprise},

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
        return redirect('liste_partenaire')
    
    roles = Role.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_partenaire.html', {'roles': roles})

#Fonction pour retourner la vue vers la page de la liste des entreprises
def liste_partenaire(request):
    if request.user.role.nom_role == 'Super admin':  # Vérifiez le rôle de l'utilisateur
        entreprises = Entreprise.objects.select_related('compte').all()
        salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()
    else:
        entreprises = Entreprise.objects.filter(creer_par=request.user).select_related('compte')
        salaries = Salarie.objects.filter(creer_par=request.user).select_related('compte').prefetch_related('competence_set')

    context = {
    'entreprises': entreprises,
    'salaries': salaries,
    }
    return render(request,'pages/admin/pages/liste/liste_partenaire.html',context)

#Fonction profile entreprise
def profile_entreprise(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = get_object_or_404(Compte, id=user_id)

    if not hasattr(user, 'role') or user.role.acce_page != "EN":
        messages.error(request, "Vous n'avez pas les droits d'accès à cette page.")
        return redirect('home_entreprise')

    try:
        entreprise_info = Entreprise.objects.get(compte=user)
    except Entreprise.DoesNotExist:
        messages.error(request, "Les informations de l'entreprise n'ont pas été trouvées.")
        return redirect('home_entreprise')

    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        nom_entreprise = request.POST.get('nom_entreprise')
        nom_agent_entreprise = request.POST.get('nom_agent_entreprise ')
        prenom_agent_entreprise = request.POST.get('prenom_agent_entreprise ')
        poste_agent = request.POST.get('poste_agent')
        secteur_activite = request.POST.get('secteur_activite')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')
        telephone = request.POST.get('telephone')
        site_web = request.POST.get('site_web')

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
            entreprise_info.nom_entreprise=nom_entreprise,
            entreprise_info.nom_agent_entreprise=nom_agent_entreprise,
            entreprise_info.poste_agent=poste_agent,
            entreprise_info.secteurActivite = secteur_activite
            entreprise_info.site_web = site_web
            entreprise_info.save()

            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('profile_entreprise')

    return render(request, 'pages/entreprise/dashboard/profile.html', {'user': user, 'entreprise_info': entreprise_info})

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
        nom_client = request.POST.get('nom_client')
        prenom_client = request.POST.get('prenom_client')
        poste_occupe = request.POST.get('poste_occupe')
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
                'poste_occupe': poste_occupe,
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
            nom_client=nom_client,
            prenom_client=prenom_client,
            poste_occupe=poste_occupe,
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
        return redirect('liste_client')
    
    roles = Role.objects.all()
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_client.html', {'entreprises': entreprises, 'roles': roles})

#Fonction pour retourner la vue vers la page de la liste des entreprises
def liste_client(request):
    if request.user.role.nom_role == 'Super admin':  # Vérifiez le rôle de l'utilisateur
        clients = Client.objects.select_related('compte').all()
        entreprises = Entreprise.objects.select_related('compte').all()
        salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()
    else:
        clients = Client.objects.filter(creer_par=request.user).select_related('compte')
        entreprises = Entreprise.objects.filter(creer_par=request.user).select_related('compte')
        salaries = Salarie.objects.filter(creer_par=request.user).select_related('compte').prefetch_related('competence_set')

    context = {
    'clients': clients,
    'entreprises': entreprises,
    'salaries': salaries,
    }
    return render(request,'pages/admin/pages/liste/liste_client.html',context)

#Fonction vers la vue du profile du client
def profile_client(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = get_object_or_404(Compte, id=user_id)

    if not hasattr(user, 'role') or user.role.acce_page != "CL":
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

    return render(request, 'pages/client/dashboard/profile.html', {'user': user, 'client_info': client_info})

#Fonction pour activé ou désactivé un compte
def statut(request, user_id):
    compte = Compte.objects.get(id=user_id)
    compte.is_active = not compte.is_active
    compte.save()
    messages.success(request, f"Le statut de {compte.nom_utilisateur} a été mis à jour.")
    # Redirection basée sur l'accès de l'utilisateur
    if compte.role.acce_page == "AD":
        return redirect('liste_admin')
    elif compte.role.acce_page == "SA":
        return redirect('liste_salarie')
    elif compte.role.acce_page == "EN":
        return redirect('liste_partenaire')
    elif compte.role.acce_page == "CL":
        return redirect('liste_client')
    if compte.role.acce_page == "GE":
        return redirect('liste_admin')
    else:
        return redirect('home_admin')

#Création de la vue pour créer les contrats 
def creer_contrat(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        type_contrat = request.POST.get('type_contrat')
        fonction_salarie = request.POST.get('fonction_salarie')
        mode_paiement = request.POST.get('mode_paiement')
        taux_horaire = request.POST.get('taux_horaire')
        heures_travail = request.POST.get('heures_travail')
        jours_travail = request.POST.get('jours_travail')
        taux_journalier = request.POST.get('taux_journalier')
        salaire_mensuel = request.POST.get('salaire_mensuel')
        salarie_id = request.POST.get('salarie')
        entreprise_id = request.POST.get('entreprise')
        client_id = request.POST.get('client')
        clauses = request.POST.getlist('clauses')

        salarie = Salarie.objects.get(id=salarie_id)
        entreprise = Entreprise.objects.get(id=entreprise_id) if entreprise_id else None
        client = Client.objects.get(id=client_id) if client_id else None

        errors = {}
        
        # Vérification de la sélection soit d'une entreprise, soit d'un client, mais pas les deux
        if not entreprise and not client:
            errors['entreprise_client'] = "Vous devez sélectionner soit une entreprise, soit un client."
        if entreprise and client:
            errors['entreprise_client'] = "Vous ne pouvez sélectionner qu'une entreprise ou un client, pas les deux."

        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        try:
            taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        except ValueError:
            errors['taux_horaire'] = "Le taux horaire doit être un nombre valide."
        try:
            heures_travail = int(heures_travail) if heures_travail else 0
        except ValueError:
            errors['heures_travail'] = "Le nombre d'heures de travail doit être un nombre entier."
        try:
            jours_travail = int(jours_travail) if jours_travail else 0
        except ValueError:
            errors['jours_travail'] = "Le nombre de jours de travail doit être un nombre entier."
        try:
            taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        except ValueError:
            errors['taux_journalier'] = "Le taux journalier doit être un nombre valide."
        try:
            salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        except ValueError:
            errors['salaire_mensuel'] = "Le salaire mensuel doit être un nombre valide."

        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Validation des valeurs négatives
        if taux_horaire < 0:
            errors['taux_horaire'] = "Le taux horaire ne peut pas être négatif."
        if heures_travail < 0:
            errors['heures_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if jours_travail < 0:
            errors['jours_travail'] = "Le nombre de jours de travail ne peut pas être négatif."
        if taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if salaire_mensuel < 0:
            errors['salaire_mensuel'] = "Le salaire mensuel ne peut pas être négatif."

        # Validation du nombre de contrats actifs
        active_contracts = Contrat.objects.filter(
            salarie=salarie,
            est_terminer=False,
            date_fin__gte=date.today()
        ).count()
        
        if active_contracts >= 2:
            errors['salarie'] = "Le salarié ne peut pas avoir plus de deux contrats en cours."
        
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_contrat.html', {
                'errors': errors,
                'salaries': Salarie.objects.all(),
                'entreprises': Entreprise.objects.all(),
                'clients': Client.objects.all(),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'fonction_salarie': fonction_salarie,
                'mode_paiement': mode_paiement,
                'taux_horaire': taux_horaire,
                'heures_travail': heures_travail,
                'jours_travail': jours_travail,
                'taux_journalier': taux_journalier,
                'salaire_mensuel': salaire_mensuel,
                'clauses': clauses,
                'salarie_id': salarie_id,
                'entreprise_id': entreprise_id,
                'client_id': client_id,
            })
        else:
            contrat = Contrat(
                date_debut=date_debut,
                date_fin=date_fin,
                type_contrat=type_contrat,
                fonction_salarie=fonction_salarie,
                mode_paiement=mode_paiement,
                taux_horaire=taux_horaire,
                heures_travail=heures_travail,
                jours_travail=jours_travail,
                taux_journalier=taux_journalier,
                salaire_mensuel=salaire_mensuel,
                salarie=salarie,
                entreprise=entreprise,
                client=client,
                creer_par=request.user
            )
            contrat.save()
        
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('liste_contrat')

    salaries = Salarie.objects.all()
    entreprises = Entreprise.objects.all()
    clients = Client.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_contrat.html', {'salaries': salaries, 'entreprises': entreprises, 'clients': clients})


#Fonction pour terminer ou laissé un contrat en cours 
def statutContrat(request, contrat_id):
    contrat = Contrat.objects.get(id=contrat_id)
    contrat.est_terminer = not contrat.est_terminer
    contrat.save()
    messages.success(request, f"Le statut du contrat a été mis à jour.")
    return redirect('Liste_contrat')

#Fonction pour retourner la vue vers la page de la liste des contrats
def liste_contrat(request):
    if request.user.role.nom_role == 'Super admin':  # Vérifiez le rôle de l'utilisateur
        contrats = Contrat.objects.prefetch_related('clause_set').all()
    else:
        contrats = Contrat.objects.filter(creer_par=request.user).prefetch_related('clause_set')

    context = {
        'contrats': contrats
    }
    return render(request, 'pages/admin/pages/liste/liste_contrat.html', context)

# Modifier un contrat
def detail_contrat(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)
    return render(request,'pages/admin/pages/liste/liste_contrat.html',contrat)

# Modifier un contrat
def modifier_contrat(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)

    if request.method == 'POST':
        salarie_id = request.POST['salarie']
        entreprise_id = request.POST.get('entreprise')  # Peut être None
        client_id = request.POST.get('client')  # Peut être None
        date_debut = request.POST['date_debut']
        date_debut = request.POST['date_debut']
        date_fin = request.POST['date_fin']
        type_contrat = request.POST['type_contrat']
        fonction_salarie=request.POST['fonction_salarie']
        mode_paiement = request.POST['mode_paiement']
        taux_horaire = request.POST.get('taux_horaire')
        heures_travail = request.POST.get('heures_travail')
        jours_travail = request.POST.get('jours_travail')
        taux_journalier = request.POST.get('taux_journalier')
        salaire_mensuel = request.POST.get('salaire_mensuel')
        
        errors = {}
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        try:
            taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        except ValueError:
            errors['taux_horaire'] = "Le taux horaire doit être un nombre valide."
        try:
            heures_travail = int(heures_travail) if heures_travail else 0
        except ValueError:
            errors['heures_travail'] = "Le nombre d'heures de travail doit être un nombre entier."
        try:
            jours_travail = int(jours_travail) if jours_travail else 0
        except ValueError:
            errors['jours_travail'] = "Le nombre de jours de travail doit être un nombre entier."
        try:
            taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        except ValueError:
            errors['taux_journalier'] = "Le taux journalier doit être un nombre valide."
        try:
            salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        except ValueError:
            errors['salaire_mensuel'] = "Le salaire mensuel doit être un nombre valide."

        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Validation des valeurs négatives
        if taux_horaire is not 0 and taux_horaire < 0:
            errors['taux_horaire'] = "Le taux horaire ne peut pas être négatif."
        if heures_travail is not 0 and heures_travail < 0:
            errors['heures_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if jours_travail is not 0 and jours_travail < 0:
            errors['jours_travail'] = "Le nombre de jours de travail ne peut pas être négatif."
        if taux_journalier is not 0 and taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if salaire_mensuel is not 0 and salaire_mensuel < 0:
            errors['salaire_mensuel'] = "Le salaire mensuel ne peut pas être négatif."
        
        if errors:
            return render(request, 'pages/admin/pages/creer/creer_contrat.html', {
                'errors': errors,
                'salaries': Salarie.objects.all(),
                'entreprises': Entreprise.objects.all(),
                'clients': Client.objects.all(),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'fonction_salarie': fonction_salarie,
                'mode_paiement': mode_paiement,
                'taux_horaire': taux_horaire,
                'heures_travail': heures_travail,
                'jours_travail': jours_travail,
                'taux_journalier': taux_journalier,
                'salaire_mensuel': salaire_mensuel,
                'salarie_id': salarie_id,
                'entreprise_id': entreprise_id,
                'client_id': client_id,
            })

        # Mettre à jour les informations du contrat
        contrat.date_debut = date_debut
        contrat.date_fin = date_fin
        contrat.type_contrat = type_contrat
        contrat.fonction_salarie = fonction_salarie
        contrat.mode_paiement = mode_paiement
        contrat.taux_horaire = taux_horaire
        contrat.heures_travail = heures_travail
        contrat.jours_travail = jours_travail
        contrat.taux_journalier = taux_journalier
        contrat.salaire_mensuel = salaire_mensuel
        contrat.salarie_id = salarie_id

        # Mettre à jour les relations entreprise/client
        contrat.entreprise_id = entreprise_id if entreprise_id else None
        contrat.client_id = client_id if client_id else None

        contrat.save()
        
        # Gestion des clauses
        existing_clauses = request.POST.getlist('clauses')
        
        # Supprimer toutes les clauses existantes
        contrat.clause_set.all().delete()
        
        # Ajouter les nouvelles clauses
        for clause_text in existing_clauses:
            if clause_text.strip():
                new_clause = Clause(contrat=contrat, clause=clause_text)
                new_clause.save()
        
        messages.success(request, 'Le contrat a été mis à jour avec succès.')
        return redirect('liste_contrat') # Rediriger vers la liste des contrats après modification
    
    entreprises = Entreprise.objects.all()
    clients = Client.objects.all()

    return render(request, 'pages/admin/pages/modifier/modifier_contrat.html', {
        'entreprises': entreprises,
        'clients': clients,
    })

#Création de la vue pour affecter un salarié 
def affecter_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    if request.method == 'POST':
        entreprise_id = request.POST['entreprise']
        date_debut = request.POST['date_debut']
        date_fin = request.POST['date_fin']
        type_contrat = request.POST['type_contrat']
        fonction_salarie=request.POST['fonction_salarie']
        mode_paiement = request.POST['mode_paiement']
        taux_horaire = request.POST.get('taux_horaire')
        heures_travail = request.POST.get('heures_travail')
        jours_travail = request.POST.get('jours_travail')
        taux_journalier = request.POST.get('taux_journalier')
        salaire_mensuel = request.POST.get('salaire_mensuel')
        client_id = request.POST.get('client')
        clauses = request.POST.getlist('clauses')

        salarie = Salarie.objects.get(id=salarie_id)
        entreprise = Entreprise.objects.get(id=entreprise_id) if entreprise_id else None
        client = Client.objects.get(id=client_id) if client_id else None
        
        errors = {}
        
        # Vérification de la sélection soit d'une entreprise, soit d'un client, mais pas les deux
        if not entreprise and not client:
            errors['entreprise_client'] = "Vous devez sélectionner soit une entreprise, soit un client."
        if entreprise and client:
            errors['entreprise_client'] = "Vous ne pouvez sélectionner qu'une entreprise ou un client, pas les deux."

        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        try:
            taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        except ValueError:
            errors['taux_horaire'] = "Le taux horaire doit être un nombre valide."
        try:
            heures_travail = int(heures_travail) if heures_travail else 0
        except ValueError:
            errors['heures_travail'] = "Le nombre d'heures de travail doit être un nombre entier."
        try:
            jours_travail = int(jours_travail) if jours_travail else 0
        except ValueError:
            errors['jours_travail'] = "Le nombre de jours de travail doit être un nombre entier."
        try:
            taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        except ValueError:
            errors['taux_journalier'] = "Le taux journalier doit être un nombre valide."
        try:
            salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        except ValueError:
            errors['salaire_mensuel'] = "Le salaire mensuel doit être un nombre valide."

        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Validation des valeurs négatives
        if taux_horaire < 0:
            errors['taux_horaire'] = "Le taux horaire ne peut pas être négatif."
        if heures_travail < 0:
            errors['heures_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if jours_travail < 0:
            errors['jours_travail'] = "Le nombre de jours de travail ne peut pas être négatif."
        if taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if salaire_mensuel < 0:
            errors['salaire_mensuel'] = "Le salaire mensuel ne peut pas être négatif."

        # Validation du nombre de contrats actifs
        active_contracts = Contrat.objects.filter(
            salarie=salarie,
            est_terminer=False,
            date_fin__gte=date.today()
        ).count()
        
        if active_contracts >= 2:
            errors['salarie'] = "Le salarié ne peut pas avoir plus de deux contrats en cours."
        
        if errors:
            return render(request, 'pages/admin/pages/liste/liste_salarie.html', {
                'errors': errors,
                'salaries': Salarie.objects.all(),
                'entreprises': Entreprise.objects.all(),
                'clients': Client.objects.all(),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'fonction_salarie': fonction_salarie,
                'mode_paiement': mode_paiement,
                'taux_horaire': taux_horaire,
                'heures_travail': heures_travail,
                'jours_travail': jours_travail,
                'taux_journalier': taux_journalier,
                'salaire_mensuel': salaire_mensuel,
                'clauses': clauses,
                'salarie_id': salarie_id,
                'entreprise_id': entreprise_id,
                'client_id': client_id,
            })
            
        contrat = Contrat.objects.create(
            salarie=salarie,
            entreprise=entreprise,
            date_debut=date_debut,
            date_fin=date_fin,
            type_contrat=type_contrat,
            fonction_salarie=fonction_salarie,
            mode_paiement=mode_paiement,
            taux_horaire=taux_horaire,
            heures_travail=heures_travail,
            jours_travail=jours_travail,
            taux_journalier=taux_journalier,
            salaire_mensuel=salaire_mensuel
        )
        contrat.save()
        
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('liste_salarie')
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/pages/liste/liste_salarie.html', {'salarie': salarie, 'entreprises': entreprises})

#Création de la vue pour affecter un salarié à une entreprise 
def affecter_entreprise_salarie(request, entreprise_id):
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    if request.method == 'POST':
        salarie_id = request.POST['salarie']
        date_debut = request.POST['date_debut']
        date_fin = request.POST['date_fin']
        type_contrat = request.POST['type_contrat']
        fonction_salarie=request.POST['fonction_salarie']
        mode_paiement = request.POST['mode_paiement']
        taux_horaire = request.POST.get('taux_horaire')
        heures_travail = request.POST.get('heures_travail')
        jours_travail = request.POST.get('jours_travail')
        taux_journalier = request.POST.get('taux_journalier')
        salaire_mensuel = request.POST.get('salaire_mensuel')
        clauses = request.POST.getlist('clauses')
        
        salarie = Salarie.objects.get(id=salarie_id)
        entreprise = Entreprise.objects.get(id=entreprise_id)
        
        errors = {}

        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        try:
            taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        except ValueError:
            errors['taux_horaire'] = "Le taux horaire doit être un nombre valide."
        try:
            heures_travail = int(heures_travail) if heures_travail else 0
        except ValueError:
            errors['heures_travail'] = "Le nombre d'heures de travail doit être un nombre entier."
        try:
            jours_travail = int(jours_travail) if jours_travail else 0
        except ValueError:
            errors['jours_travail'] = "Le nombre de jours de travail doit être un nombre entier."
        try:
            taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        except ValueError:
            errors['taux_journalier'] = "Le taux journalier doit être un nombre valide."
        try:
            salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        except ValueError:
            errors['salaire_mensuel'] = "Le salaire mensuel doit être un nombre valide."

        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Validation des valeurs négatives
        if taux_horaire < 0:
            errors['taux_horaire'] = "Le taux horaire ne peut pas être négatif."
        if heures_travail < 0:
            errors['heures_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if jours_travail < 0:
            errors['jours_travail'] = "Le nombre de jours de travail ne peut pas être négatif."
        if taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if salaire_mensuel < 0:
            errors['salaire_mensuel'] = "Le salaire mensuel ne peut pas être négatif."

        # Validation du nombre de contrats actifs
        active_contracts = Contrat.objects.filter(
            salarie=salarie,
            est_terminer=False,
            date_fin__gte=date.today()
        ).count()
        
        if active_contracts >= 2:
            errors['salarie'] = "Le salarié ne peut pas avoir plus de deux contrats en cours."
        
        if errors:
            return render(request, 'pages/admin/pages/liste/liste_partenaire.html', {
                'errors': errors,
                'salaries': Salarie.objects.all(),
                'entreprises': Entreprise.objects.all(),
                'clients': Client.objects.all(),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'fonction_salarie': fonction_salarie,
                'mode_paiement': mode_paiement,
                'taux_horaire': taux_horaire,
                'heures_travail': heures_travail,
                'jours_travail': jours_travail,
                'taux_journalier': taux_journalier,
                'salaire_mensuel': salaire_mensuel,
                'clauses': clauses,
                'salarie_id': salarie_id,
                'entreprise_id': entreprise_id,
            })
        
        contrat = Contrat.objects.create(
            salarie=salarie,
            entreprise=entreprise,
            date_debut=date_debut,
            date_fin=date_fin,
            type_contrat=type_contrat,
            fonction_salarie=fonction_salarie,
            mode_paiement=mode_paiement,
            taux_horaire=taux_horaire,
            heures_travail=heures_travail,
            jours_travail=jours_travail,
            taux_journalier=taux_journalier,
            salaire_mensuel=salaire_mensuel
        )
        contrat.save()
        
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('liste_partenaire')
    salaries = Salarie.objects.all()
    return render(request, 'pages/admin/pages/liste/liste_partenaire.html', {'salarie': salarie, 'salaries': salaries})

#Création de la vue pour affecter un salarié à une client 
def affecter_client_salarie(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        salarie_id = request.POST['salarie']
        date_debut = request.POST['date_debut']
        date_fin = request.POST['date_fin']
        type_contrat = request.POST['type_contrat']
        fonction_salarie=request.POST['fonction_salarie']
        mode_paiement = request.POST['mode_paiement']
        taux_horaire = request.POST.get('taux_horaire')
        heures_travail = request.POST.get('heures_travail')
        jours_travail = request.POST.get('jours_travail')
        taux_journalier = request.POST.get('taux_journalier')
        salaire_mensuel = request.POST.get('salaire_mensuel')
        clauses = request.POST.getlist('clauses')
        
        salarie = Salarie.objects.get(id=salarie_id)
        client = Client.objects.get(id=client_id)
        
        errors = {}

        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        try:
            taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        except ValueError:
            errors['taux_horaire'] = "Le taux horaire doit être un nombre valide."
        try:
            heures_travail = int(heures_travail) if heures_travail else 0
        except ValueError:
            errors['heures_travail'] = "Le nombre d'heures de travail doit être un nombre entier."
        try:
            jours_travail = int(jours_travail) if jours_travail else 0
        except ValueError:
            errors['jours_travail'] = "Le nombre de jours de travail doit être un nombre entier."
        try:
            taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        except ValueError:
            errors['taux_journalier'] = "Le taux journalier doit être un nombre valide."
        try:
            salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        except ValueError:
            errors['salaire_mensuel'] = "Le salaire mensuel doit être un nombre valide."

        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            errors['date_debut'] = "La date de début ne peut pas être supérieure à la date de fin."
        if date_debut and date_fin and date_fin < date_debut:
            errors['date_fin'] = "La date de fin ne peut pas être inférieure à la date de début."
        
        # Validation des valeurs négatives
        if taux_horaire < 0:
            errors['taux_horaire'] = "Le taux horaire ne peut pas être négatif."
        if heures_travail < 0:
            errors['heures_travail'] = "Le nombre d'heures de travail ne peut pas être négatif."
        if jours_travail < 0:
            errors['jours_travail'] = "Le nombre de jours de travail ne peut pas être négatif."
        if taux_journalier < 0:
            errors['taux_journalier'] = "Le taux journalier ne peut pas être négatif."
        if salaire_mensuel < 0:
            errors['salaire_mensuel'] = "Le salaire mensuel ne peut pas être négatif."

        # Validation du nombre de contrats actifs
        active_contracts = Contrat.objects.filter(
            salarie=salarie,
            est_terminer=False,
            date_fin__gte=date.today()
        ).count()
        
        if active_contracts >= 2:
            errors['salarie'] = "Le salarié ne peut pas avoir plus de deux contrats en cours."
        
        if errors:
            return render(request, 'pages/admin/pages/liste/liste_client.html', {
                'errors': errors,
                'salaries': Salarie.objects.all(),
                'clients': Client.objects.all(),
                'date_debut': date_debut,
                'date_fin': date_fin,
                'type_contrat': type_contrat,
                'fonction_salarie': fonction_salarie,
                'mode_paiement': mode_paiement,
                'taux_horaire': taux_horaire,
                'heures_travail': heures_travail,
                'jours_travail': jours_travail,
                'taux_journalier': taux_journalier,
                'salaire_mensuel': salaire_mensuel,
                'clauses': clauses,
                'salarie_id': salarie_id,
                'client_id': client_id,
            })
        
        contrat = Contrat.objects.create(
            salarie=salarie,
            client=client,
            date_debut=date_debut,
            date_fin=date_fin,
            type_contrat=type_contrat,
            fonction_salarie=fonction_salarie,
            mode_paiement=mode_paiement,
            taux_horaire=taux_horaire,
            heures_travail=heures_travail,
            jours_travail=jours_travail,
            taux_journalier=taux_journalier,
            salaire_mensuel=salaire_mensuel
        )
        contrat.save()

        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('liste_client')
    salaries = Salarie.objects.all()
    return render(request, 'pages/admin/pages/liste/liste_client.html', {'salarie': salarie, 'salaries': salaries})

#Fonction me permettant d'avoir tout les contrat en relations en avec un salarié
def contrats_en_cours(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    contrats = Contrat.objects.filter(salarie=salarie, est_terminer=False)
    return render(request, 'pages/admin/pages/liste/liste_contrat_en_cours.html', {'contrats': contrats, 'salarie': salarie})

def contrats_termines(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    contrats = Contrat.objects.filter(salarie=salarie, est_terminer=True)
    return render(request, 'pages/admin/pages/liste/liste_contrat_terminer.html', {'contrats': contrats, 'salarie': salarie})

#Fonction me permettant d'avoir tout les contrat en relations en avec un  partenaire
def contrats_en_cours_partenaire(request, entreprise_id):
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    contrats = Contrat.objects.filter(entreprise=entreprise, est_terminer=False)
    return render(request, 'pages/admin/pages/liste/liste_contrat_en_cours_partenaire.html', {'contrats': contrats, 'entreprise': entreprise})

def contrats_termines_partenaire(request, entreprise_id):
    entreprise = get_object_or_404(Entreprise, id=entreprise_id)
    contrats = Contrat.objects.filter(entreprise=entreprise, est_terminer=True)
    return render(request, 'pages/admin/pages/liste/liste_contrat_terminer_partenaire.html', {'contrats': contrats, 'entreprise': entreprise})

#Fonction me permettant d'avoir tout les contrat en relations en avec un  client
def contrats_en_cours_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    contrats = Contrat.objects.filter(client=client, est_terminer=False)
    return render(request, 'pages/admin/pages/liste/liste_contrat_en_cours_client.html', {'contrats': contrats, 'client': client})

def contrats_termines_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    contrats = Contrat.objects.filter(client=client, est_terminer=True)
    return render(request, 'pages/admin/pages/liste/liste_contrat_terminer_client.html', {'contrats': contrats, 'client': client})

#Création de la vue pour affecter un salarié 
def editer_fiche_paie(request, salarie_id):
    return render(request, 'pages/admin/pages/liste/liste_salarie.html')

#Fonction pour retourner la vue vers la page de la liste des fiches de paies
def liste_fichePaie(request):
    return render(request, 'pages/admin/pages/liste/liste_fichepaie.html')

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
def envoyer_contract_pdf(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    context = {
        'contrat': contrat,
        'date': datetime.datetime.today()  # Ajout de la date dans le contexte
    }
    
    template = get_template('pages/admin/pages/pdf/contrat.html')
    html = template.render(context)
    
    # Options du format PDF
    options = {
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        "enable-local-file-access": ""
    }
    
    # Générer le PDF
    pdf = pdfkit.from_string(html, False, options, configuration=config)
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f"attachment; filename=contrat_{contrat.id}.pdf"
    
    if pdf:
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        
        subject = "Votre contrat de travail a été établi avec succès"
        message = "Veuillez trouver ci-joint votre contrat de travail."
        
        email = EmailMessage(
            subject, 
            message, 
            settings.EMAIL_HOST_USER, 
            [contrat.salarie.compte.email, contrat.entreprise.compte.email]
        )
        
        email.attach(f"contrat_{contrat.id}.pdf", pdf, 'application/pdf')
        email.send()
    
    return response

