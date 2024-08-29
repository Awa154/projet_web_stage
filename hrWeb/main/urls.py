from django.urls import path
from .views import *

urlpatterns = [
    #Accueil
    path('', home, name="home"),
    
    
    #Rôles
    path('creer_role', creer_role, name="creer_role"),
    path('modifier_role/<int:role_id>/',modifier_role, name='modifier_role'),
    path('supprimer_role/<int:role_id>/',supprimer_role, name='supprimer_role'),
    path('liste_roles', liste_roles, name="liste_roles"), 
    
    
    #départements
    path('creer_departement/<int:entreprise_id>/', creer_departement, name="creer_departement"),
    path('modifier_departement/<int:departement_id>/',modifier_departement, name='modifier_departement'),
    path('supprimer_departement/<int:departement_id>/',supprimer_departement, name='supprimer_departement'),
    path('liste_departements/<int:entreprise_id>/', liste_departements, name="liste_departements"),
    path('get_departements/', get_departements, name='get_departements'),
    
    
    #Authentification
    path('connexion', connexion, name="connexion"),
    path('deconnexion', deconnexion, name="deconnexion"),
    path('oublier_mot_de_passe', oublier_mot_de_passe, name="oublier_mot_de_passe"),
    path('changer_mot_de_passe', changer_mot_de_passe, name="changer_mot_de_passe"),
    path('statut/<int:user_id>/', statut, name='statut'),
    path('annuler_changer_mot_de_passe', annuler_changer_mot_de_passe, name='annuler_changer_mot_de_passe'),
    
    
    #Compte admin
    path('home_admin', home_admin, name="home_admin"),
    path('profile_admin', profile_admin, name="profile_admin"),
    
    
    #Admins
    path('creer_admin', creer_admin, name="creer_admin"),
    path('liste_admins', liste_admins, name="liste_admins"),
    
    
    #Compte salarié
    path('home_salarie', home_salarie, name="home_salarie"),
    path('profile_salarie', profile_salarie, name="profile_salarie"),
    path('liste_contrats_salarie', liste_contrats_salarie, name="liste_contrats_salarie"),
    path('liste_fiches_de_paie_salarie', liste_fiches_de_paie_salarie, name="liste_fiches_de_paie_salarie"),
    
    
    #Salariés
    path('creer_salarie', creer_salarie, name="creer_salarie"),
    path('modifier_contrat_salarie/<int:contrat_id>/<int:salarie_id>/',modifier_contrat_salarie, name='modifier_contrat_salarie'),
    path('liste_salaries', liste_salaries, name="liste_salaries"),
    path('liste_contrats_un_salarie/<int:salarie_id>/', liste_contrats_un_salarie, name="liste_contrats_un_salarie"),
    path('supprimer_competence/<int:competence_id>/',supprimer_competence, name='supprimer_competence'),
    
    
    #Compte entreprise partenaire
    path('home_partenaire', home_partenaire, name="home_partenaire"),
    path('profile_partenaire', profile_partenaire, name="profile_partenaire"),
    path('liste_salaries_contrats_partenaire', liste_salaries_contrats_partenaire, name="liste_salaries_contrats_partenaire"),
    path('liste_fiches_de_paie_partenaire', liste_fiches_de_paie_partenaire, name="liste_fiches_de_paie_partenaire"),
    path('demande_partenaire', demande_partenaire, name='demande_partenaire'),
    path('mes_demandes_partenaire', mes_demandes_partenaire, name='mes_demandes_partenaire'),
    
    
    #Entreprise partenaires
    path('creer_partenaire', creer_partenaire, name="creer_partenaire"),
    path('liste_partenaires', liste_partenaires, name="liste_partenaires"),
    
    
    #Compte client
    path('home_client', home_client, name="home_client"),
    path('profile_client', profile_client, name="profile_client"),
    path('liste_salaries_contrats_client', liste_salaries_contrats_client, name="liste_salaries_contrats_en_cours_client"),
    path('liste_fiches_de_paie_client', liste_fiches_de_paie_client, name="liste_fiches_de_paie_client"),
    path('demande_client', demande_client, name='demande_client'),
    path('mes_demandes_client', mes_demandes_client, name='mes_demandes_client'),
    
    
    #Clients
    path('creer_client', creer_client, name="creer_client"),
    path('liste_clients', liste_clients, name="liste_clients"),
    
    
    #Entreprises
    path('creer_entreprise', creer_entreprise, name="creer_entreprise"),
    path('modifier_entreprise/<int:entreprise_id>/',modifier_entreprise, name='modifier_entreprise'),
    path('supprimer_entreprise/<int:entreprise_id>/',supprimer_entreprise, name='supprimer_entreprise'),
    path('liste_entreprises', liste_entreprises, name="liste_entreprises"),
    
    
    #Affectations
    path('affecter_salarie/<int:salarie_id>/', affecter_salarie, name="affecter_salarie"),
    path('modifier_affectation/<int:affectation_id>/', modifier_affectation, name="modifier_affectation"),
    path('liste_contrats_affectations', liste_contrats_affectations, name="liste_contrats_affectations"),
    path('supprimer_affectation/<int:affectation_id>/',supprimer_affectation, name='supprimer_affectation'),
    
    
    #Documents contrats
    path('editer_doc_contrat/<int:contrat_id>/', editer_doc_contrat, name="editer_doc_contrat"),
    path('liste_doc_contrats', liste_doc_contrats, name="liste_doc_contrats"),  
    path('detail_contrat/<int:contrat_id>/', detail_contrat, name="detail_contrat"), 
    
    
    #Fiches de paie
    path('editer_fichePaie/<int:salarie_id>/', editer_fichePaie, name='editer_fichePaie'),
    path('valider_fichePaie/<int:salarie_id>/', valider_fichePaie, name="valider_fichePaie"), 
    path('liste_fichesPaie', liste_fichesPaie , name='liste_fichesPaie'),
    path('liste_fiches_de_paie_salarie/<int:salarie_id>/', liste_fiches_de_paie_salarie , name='liste_fiches_de_paie_salarie'),
    path('statut_fichePaie/<int:fiche_id>/', statut_fichePaie, name='statut_fiche_de_paie'),
    
    path('editer_fichePaie_affectation/<int:affectation_id>/', editer_fichePaie_affectation, name='editer_fichePaie_affectation'),
    path('liste_fichesPaie_affectation',liste_fichesPaie_affectation , name='liste_fichesPaie_affectation'),
    path('detail_fiche_de_paie_affectation/<int:affectation_id>/', detail_fiche_de_paie_affectation, name="detail_fiche_de_paie_affectation"), 
    
    
    #Email
    path('configurer_email', configurer_email, name="configurer_email"),
    
    
    #Demandes
    path('liste_demandes',liste_demandes, name='liste_demandes'),
    path('changer_statut_demande',changer_statut_demande, name='changer_statut_demande'),
    
    
    
    #PDF
    path('envoyer_contrat_pdf/<int:contrat_id>/', envoyer_contrat_pdf, name='envoyer_contrat_pdf'),
    path('envoyer_contrat_pdf_paie_affectation/<int:affectation_id>/', envoyer_contrat_pdf_paie_affectation, name='envoyer_contrat_pdf_paie_affectation')
    
]

