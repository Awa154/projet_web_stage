from celery import shared_task
from .models import Contrat

@shared_task
def verifier_contrats():
    """
    Vérifie tous les contrats pour voir s'ils sont sur le point d'expirer ou s'ils sont déjà arrivés à terme.
    """
    contrats = Contrat.objects.all()
    for contrat in contrats:
        contrat.envoyer_alerte_expiration()
        contrat.verifier_et_mettre_a_jour_statut()
