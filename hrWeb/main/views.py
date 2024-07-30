from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse

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

#Création de la vue pour créer un département
def creer_departement(request):
    if request.method == 'POST':
        nom_dep = request.POST['nom_dep']

        departement = Departement.objects.create(
            nom_dep=nom_dep,
        )
        messages.success(request, 'Le département a été ajouté avec succès.')
        return redirect('creer_departement')

    return render(request, 'pages/admin/pages/creer/creer_departement.html')

#Création de la vue pour créer un rôle
def creer_role(request):
    if request.method == 'POST':
        nom_role = request.POST['nom_role']
        niv_permission = request.POST['niv_permission']
        acce_page = request.POST['acce_page']

        role = Role.objects.create(
            nom_role=nom_role,
            niv_permission=niv_permission,
            acce_page=acce_page
        )
        messages.success(request, 'Le rôle a été créé avec succès.')
        return redirect('creer_role')

    return render(request, 'pages/admin/pages/creer/creer_role.html')

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
        
        # Valider les données
        errors = []
        # Vérifier l'unicité de l'email et du contact
        if Compte.objects.filter(email=email).exists():
            errors.append("Un utilisateur avec cet email existe déjà.")
        if Compte.objects.filter(telephone=telephone).exists():
            errors.append("Un utilisateur avec ce contact existe déjà.")
        
        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('creer_admin')
        
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            sexe=sexe,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )
        
        nom_admin = request.POST['nom_admin']
        prenom_admin = request.POST['prenom_admin']

        Admin.objects.create(
            compte=compte,
            nom_admin=nom_admin,
            prenom_admin=prenom_admin,
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
        return redirect('creer_admin')
    
    roles = Role.objects.all()
    departements = Departement.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_admin.html', {'departements': departements, 'roles': roles})

# Fonction pour retourner la vue vers la page de création de salarié
def creer_salarie(request):
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
        
        # Valider les données
        errors = []
        # Vérifier l'unicité de l'email et du contact
        if Compte.objects.filter(email=email).exists():
            errors.append("Un utilisateur avec cet email existe déjà.")
        if Compte.objects.filter(telephone=telephone).exists():
            errors.append("Un utilisateur avec ce contact existe déjà.")
        
        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('creer_salarie')
        
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            sexe=sexe,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )
        
        # Créer le modèle associé basé sur le rôle de l'utilisateur
        nom_salarie = request.POST.get('nom_salarie')
        prenom_salarie = request.POST.get('prenom_salarie')
        dateNaissance = request.POST.get('dateNaissance')
        annee_exp = request.POST.get('annee_exp')
        departement_id = request.POST.get('departement')
        
        try:
            departement = Departement.objects.get(id=departement_id)
        except Departement.DoesNotExist:
            messages.error(request, "Le département sélectionné n'existe pas.")
            return redirect('creer_salarie')
        
        salarie = Salarie.objects.create(
            compte=compte,
            nom_salarie=nom_salarie,
            prenom_salarie=prenom_salarie,
            dateNaissance=dateNaissance,
            annee_exp=annee_exp,
            departement=departement
        )

        competences = request.POST.getlist('competences')
        for competence in competences:
            Competence.objects.create(salarie=salarie, competence=competence)
            
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
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        heures_travail = int(heures_travail) if heures_travail else 0
        jours_travail = int(jours_travail) if jours_travail else 0
        taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        
        entreprise = Entreprise.objects.get(id=entreprise_id)

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
        )
        contrat.save()
        
        clauses = request.POST.getlist('clauses')
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)
        
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
        return redirect('creer_salarie')
    
    roles = Role.objects.all()
    departements = Departement.objects.all()
    entreprises = Entreprise.objects.all()
    
    info_salarie = {
        'roles': roles,
        'departements': departements,
        'entreprises':entreprises,
    } 

    return render(request, 'pages/admin/pages/creer/creer_salarie.html', info_salarie)

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
        
        # Valider les données
        errors = []
        # Vérifier l'unicité de l'email et du contact
        if Compte.objects.filter(email=email).exists():
            errors.append("Un utilisateur avec cet email existe déjà.")
        if Compte.objects.filter(telephone=telephone).exists():
            errors.append("Un utilisateur avec ce contact existe déjà.")
        
        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('creer_partenaire')
        
        compte = Compte.objects.create(
            nom_utilisateur=nom_utilisateur,
            mot_de_passe=make_password(mot_de_passe),
            email=email,
            adresse=adresse,
            telephone=telephone,
            role=role,
        )
        
        # Créer le modèle associé basé sur le rôle de l'utilisateur
        nom_entreprise = request.POST.get('nom_entreprise')
        nom_agent_entreprise = request.POST.get('nom_agent_entreprise ')
        prenom_agent_entreprise = request.POST.get('prenom_agent_entreprise ')
        poste_agent = request.POST.get('poste_agent')
        secteur_activite = request.POST.get('secteur_activite')
        site_web = request.POST.get('site_web')
        
        Entreprise.objects.create(
            compte=compte,
            nom_entreprise=nom_entreprise,
            nom_agent_entreprise=nom_agent_entreprise,
            poste_agent=poste_agent,
            prenom_agent_entreprise =prenom_agent_entreprise ,
            secteurActivite=secteur_activite,
            site_web=site_web,
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
        return redirect('creer_partenaire')
    
    roles = Role.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_partenaire.html', {'roles': roles})

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
        errors = []
        if Compte.objects.filter(email=email).exists():
            errors.append("Un utilisateur avec cet email existe déjà.")
        if Compte.objects.filter(telephone=telephone).exists():
            errors.append("Un utilisateur avec ce contact existe déjà.")
        
        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('creer_client')
        
        try:
            role = Role.objects.get(id=role_id)
            entreprise_affilier = Entreprise.objects.get(id=entreprise_id)
        except Role.DoesNotExist:
            messages.error(request, "Rôle invalide.")
            return redirect('creer_client')
        except Entreprise.DoesNotExist:
            messages.error(request, "Entreprise invalide.")
            return redirect('creer_client')
        
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
            entreprise_affilier=entreprise_affilier
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
        return redirect('creer_client')
    
    roles = Role.objects.all()
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_client.html', {'entreprises': entreprises, 'roles': roles})

def connexion(request):
    if request.method == 'POST':
        nom_utilisateur = request.POST.get('nom_utilisateur')
        mot_de_passe = request.POST.get('mot_de_passe')

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

            if compte.role.acce_page == 'AD':
                return redirect('home_admin')
            elif compte.role.acce_page == 'SA':
                return redirect('home_salarie')
            elif compte.role.acce_page == 'EN':
                return redirect('home_entreprise')
            elif compte.role.acce_page == 'CL':
                return redirect('home_client')
            else:
                messages.error(request, "Aucune page d'accès définie pour ce rôle.")
                return redirect('connexion')
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
            else:
                return redirect('connexion')

    return render(request, 'pages/auth/pages/change_password.html')

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
    else:
        return redirect('home_admin')

#Création de la vue pour créer les contrats 
def creer_contrat(request):
    if request.method == 'POST':
        salarie_id = request.POST['salarie']
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
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        heures_travail = int(heures_travail) if heures_travail else 0
        jours_travail = int(jours_travail) if jours_travail else 0
        taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        
        salarie = Salarie.objects.get(id=salarie_id)
        entreprise = Entreprise.objects.get(id=entreprise_id)

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
        
        clauses = request.POST.getlist('clauses')
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('creer_contrat')
    salaries = Salarie.objects.all()
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/pages/creer/creer_contrat.html', {'salaries': salaries, 'entreprises': entreprises})

#Fonction pour terminer ou laissé un contrat en cours 
def statutContrat(request, contrat_id):
    contrat = Contrat.objects.get(id=contrat_id)
    contrat.est_terminer = not contrat.est_terminer
    contrat.save()
    messages.success(request, f"Le statut du contrat a été mis à jour.")
    return redirect('Liste_contrat')

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
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        heures_travail = int(heures_travail) if heures_travail else 0
        jours_travail = int(jours_travail) if jours_travail else 0
        taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        
        entreprise = Entreprise.objects.get(id=entreprise_id)

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
        
        clauses = request.POST.getlist('clauses')
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
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        heures_travail = int(heures_travail) if heures_travail else 0
        jours_travail = int(jours_travail) if jours_travail else 0
        taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        
        salarie = Salarie.objects.get(id=salarie_id)

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
        
        clauses = request.POST.getlist('clauses')
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
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        heures_travail = int(heures_travail) if heures_travail else 0
        jours_travail = int(jours_travail) if jours_travail else 0
        taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        
        salarie = Salarie.objects.get(id=salarie_id)

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
        
        clauses = request.POST.getlist('clauses')
        for clause in clauses:
            Clause.objects.create(contrat=contrat, clause=clause)

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('liste_client')
    salaries = Salarie.objects.all()
    return render(request, 'pages/admin/pages/liste/liste_client.html', {'salarie': salarie, 'salaries': salaries})

#Création de la vue pour affecter un salarié 
def editer_fiche_paie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    if request.method == 'POST':
        contrat_id = request.POST['contrat']
        datePaiement = request.POST['datePaiement']
        echeance = request.POST['echeance']
        detail = request.POST['detail']
        montant = calculer_montant_final()
        statut = request.POST['statut']
        
        contrat = Contrat.objects.get(id=contrat_id)

        fiche_paie = FicheDePaie.objects.create(
            salarie=salarie,
            contrat=contrat,
            datePaiement=datePaiement,
            echeance=echeance,
            detail=detail,
            montant=montant,
            statut=statut
        )
        fiche_paie.save()

        messages.success(request, 'Le contrat a été établie avec succès.')
        return redirect('affecter_salare')
    entreprises = Entreprise.objects.all()
    return render(request, 'pages/admin/pages/liste/liste_salarie.html', {'salarie': salarie, 'entreprises': entreprises})

#Fonction pour retourner la vue vers la page de la liste des administrateurs
def liste_admin(request):
    admins = Admin.objects.select_related('compte').all()
    
    # Recherche
    query = request.GET.get('q')
    if query:
        admins = admins.filter(
            Q(nom_admin__icontains=query)|
            Q(prenom_admin__icontains=query)
        )

    context = {
        'admins': admins,
    }
    return render(request,'pages/admin/pages/liste/liste_admin.html', context)

#Fonction pour retourner la vue vers la page de la liste des salariés
def liste_salarie(request):
    salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()
    entreprises = Entreprise.objects.all()
    # Recherche
    query = request.GET.get('q')
    if query:
        salaries = salaries.filter(
            Q(nom_salarie__icontains=query)|
            Q(prenom_salarie__icontains=query)|
            Q(dateEmbauche__icontains=query)|
            Q(competence_set__competence__icontains=query)
        )

    context = {
        'salaries': salaries,
        'entreprises':entreprises
    }
    return render(request,'pages/admin/pages/liste/liste_salarie.html', context)

#Fonction pour retourner la vue vers la page de la liste des entreprises
def liste_partenaire(request):
    entreprises = Entreprise.objects.select_related('compte').all()
    salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()

    # Recherche
    query = request.GET.get('q')
    if query:
        entreprises = entreprises.filter(
            Q(nom__icontains=query)
        )

    context = {
    'entreprises': entreprises,
    'salaries': salaries,
    }
    return render(request,'pages/admin/pages/liste/liste_partenaire.html',context)

#Fonction pour retourner la vue vers la page de la liste des entreprises
def liste_client(request):
    clients = Client.objects.select_related('compte').all()
    entreprises = Entreprise.objects.select_related('compte').all()
    salaries = Salarie.objects.select_related('compte').prefetch_related('competence_set').all()

    # Recherche
    query = request.GET.get('q')
    if query:
        clients = clients.filter(
            Q(nom__icontains=query)
        )

    context = {
    'clients': clients,
    'entreprises': entreprises,
    'salaries': salaries,
    }
    return render(request,'pages/admin/pages/liste/liste_client.html',context)

#Fonction pour retourner la vue vers la page de la liste des contrats
def liste_contrat(request):
    contrats = Contrat.objects.prefetch_related('clause_set').all()

    # Recherche
    query = request.GET.get('q')
    if query:
        contrats = contrats.filter(
            Q(date_debut__icontains=query)|
            Q(date_fin__icontains=query)
        )

    context = {
    'contrats': contrats
    }
    return render(request,'pages/admin/pages/liste/liste_contrat.html',context)

#Fonction pour retourner la vue vers la page de la liste des fiches de paies
def liste_fichePaie(request):
    departements = Departement.objects.annotate(total_employes=Count('salarie'))
    return render(request, 'pages/admin/pages/liste/liste_fichepaie.html', {'departements': departements})

#Fonction pour retourner la vue vers la page de la liste des contrats
def liste_departements(request):
    departements = Departement.objects.annotate(total_employes=Count('salarie'))
    return render(request, 'pages/admin/pages/liste/liste_departement.html', {'departements': departements})

#Fonction pour retourner la vue vers la page de la liste des salariés
def liste_role(request):
    roles = Role.objects.all()
    
    # Recherche
    query = request.GET.get('q')
    if query:
        roles = roles.filter(
            Q(nom_role__icontains=query)
        )

    context = {
        'roles': roles,
    }
    return render(request,'pages/admin/pages/liste/liste_role.html', context)

# Modifier un département
def modifier_departement(request, departement_id):
    departement = get_object_or_404(Departement, id=departement_id)

    if request.method == 'POST':
        nom_dep = request.POST.get('nom_dep')
        departement.nom_dep = nom_dep
        departement.save()
        messages.success(request, 'Le département a été mis à jour avec succès.')
        return redirect('liste_departements')   # Rediriger vers la liste des départements après modification

    return render(request, 'pages/admin/pages/liste/liste_departement.html', {'departement': departement})

# Modifier un rôle
def modifier_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)

    if request.method == 'POST':
        nom_role = request.POST.get('nom_role')
        niv_permission = request.POST.get('niv_permission')
        acce_page = request.POST.get('acce_page')
        role.nom_role = nom_role
        role.niv_permission = niv_permission
        role.acce_page = acce_page
        role.save()
        
        messages.success(request, 'Le rôle a été mis à jour avec succès.')
        return redirect('liste_role') # Rediriger vers la liste des rôles après modification

    return render(request, 'pages/admin/pages/liste/liste_role.html', {'role': role})

# Modifier un contrat
def modifier_contrat(request, contrat_id):
    contrat = get_object_or_404(Contrat, id=contrat_id)

    if request.method == 'POST':
        salarie_id = request.POST['salarie']
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
        
        # Convertir les champs numériques ou définir None si vide, en remplaçant les virgules par des points
        taux_horaire = float(taux_horaire.replace(',', '.')) if taux_horaire else 0
        heures_travail = int(heures_travail) if heures_travail else 0
        jours_travail = int(jours_travail) if jours_travail else 0
        taux_journalier = float(taux_journalier.replace(',', '.')) if taux_journalier else 0
        salaire_mensuel = float(salaire_mensuel.replace(',', '.')) if salaire_mensuel else 0
        
        contrat.date_debut = date_debut
        contrat.date_fin = date_fin
        contrat.type_contrat = type_contrat
        contrat.fonction_salarie=fonction_salarie
        contrat.mode_paiement = mode_paiement
        contrat.taux_horaire = taux_horaire
        contrat.heures_travail = heures_travail
        contrat.taux_journalier = taux_journalier
        contrat.jours_travail = jours_travail
        contrat.salaire_mensuel = salaire_mensuel
        contrat.salarie_id = salarie_id
        contrat.entreprise_id = entreprise_id
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

    return render(request, 'pages/admin/pages/liste/liste_contrat.html', {'contrat': contrat})

# Modifier un salarié
def modifier_salarie(request, salarie_id):
    salarie = get_object_or_404(Salarie, id=salarie_id)
    
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
        
        messages.success(request, 'Le salarie a été mis à jour avec succès.')
        return redirect('liste_salarie') # Rediriger vers la liste des salaries après modification

    return render(request, 'pages/admin/pages/liste/liste_salarie.html', {'salarie': salarie})

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

