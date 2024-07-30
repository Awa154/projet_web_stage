from django.urls import path
from .views import *

urlpatterns = [
    #Route vers la page d'accueil
    path('', home, name="home"),
    
    #Route vers les pages concernant l'authentification
    path('connexion', connexion, name="connexion"),
    path('deconnexion', deconnexion, name="deconnexion"),
    path('oublier_mot_de_passe', oublier_mot_de_passe, name="oublier_mot_de_passe"),
    path('changer_mot_de_passe', changer_mot_de_passe, name="changer_mot_de_passe"),
    path('statut/<int:user_id>/', statut, name='statut'),
    
    #Route vers les vue de l'admin
    path('home_admin', home_admin, name="home_admin"),
    path('creer_admin', creer_admin, name="creer_admin"),
    path('profile_admin', profile_admin, name="profile_admin"),
    path('liste_admin', liste_admin, name="liste_admin"),
    
    #Route vers les vue du compte salarié
    path('home_salarie', home_salarie, name="home_salarie"),
    path('profile_salarie', profile_salarie, name="profile_salarie"),
    
    #Route vers les vue du compte entreprise
    path('home_entreprise', home_entreprise, name="home_entreprise"),
    path('profile_entreprise', profile_entreprise, name="profile_entreprise"),
    
    #Route vers les vue du compte client
    path('home_client', home_client, name="home_client"),
    path('profile_client', profile_client, name="profile_client"),
    
    #Route vers les vue de la gestion des rôles et départements par l'admin
    path('creer_departement', creer_departement, name="creer_departement"),
    path('creer_role', creer_role, name="creer_role"),
    path('modifier_departement/<int:departement_id>/',modifier_departement, name='modifier_departement'),
    path('modifier_role/<int:role_id>/',modifier_role, name='modifier_role'),
    path('liste_departements', liste_departements, name="liste_departements"),
    path('liste_role', liste_role, name="liste_role"), 
    
    #Route vers les vue de la gestion des salariés par l'admin
    path('creer_salarie', creer_salarie, name="creer_salarie"),
    path('modifier_salarie/<int:salarie_id>/',modifier_salarie, name='modifier_salarie'),
    path('affecter_salarie/<int:salarie_id>/', affecter_salarie, name="affecter_salarie"),
    path('editer_fiche_paie/<int:salarie_id>/', editer_fiche_paie, name="editer_fiche_paie"),
    path('liste_salarie', liste_salarie, name="liste_salarie"),
    
    #Route vers les vue de la gestion des entreprises et clients par l'admin
    path('creer_partenaire', creer_partenaire, name="creer_partenaire"),
    path('creer_client', creer_client, name="creer_client"),
    path('affecter_entreprise_salarie/<int:entreprise_id>/', affecter_entreprise_salarie, name="affecter_entreprise_salarie"),
    path('affecter_client_salarie/<int:client_id>/', affecter_client_salarie, name="affecter_client_salarie"),
    path('liste_partenaire', liste_partenaire, name="liste_partenaire"),
    path('liste_client', liste_client, name="liste_client"),
    path('contrats_en_cours_partenaire/<int:entreprise_id>/', contrats_en_cours_partenaire, name="contrats_en_cours_partenaire"),
    path('contrats_termines_partenaire/<int:entreprise_id>/', contrats_termines_partenaire, name="contrats_termines_partenaire"),
    path('contrats_en_cours_client/<int:client_id>/', contrats_en_cours_client, name="contrats_en_cours_client"),
    path('contrats_termines_client/<int:client_id>/', contrats_termines_client, name="contrats_termines_client"),  
    
    #Route vers les vue de la gestion des contrats par l'admin
    path('creer_contrat', creer_contrat, name="creer_contrat"),
    path('statutContrat/<int:contrat_id>/', statutContrat, name='statutContrat'),
    path('modifier_contrat/<int:contrat_id>/',modifier_contrat, name='modifier_contrat'),
    path('liste_contrat', liste_contrat, name="liste_contrat"),
    path('contrats_en_cours/<int:salarie_id>/', contrats_en_cours, name="contrats_en_cours"),
    path('contrats_termines/<int:salarie_id>/', contrats_termines, name="contrats_termines"),
    path('envoyer_contract_pdf/<int:contrat_id>/', envoyer_contract_pdf, name='envoyer_contract_pdf'),
    
    #Route vers vues de gestion de fiche de paies gérer par l'admin
    path('liste_fichePaie', liste_fichePaie, name="liste_fichePaie"), 
    
    #Route vers les vues de configurations d'email
    path('configurer_email', configurer_email, name="configurer_email"),
]

