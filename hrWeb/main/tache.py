# tasks.py

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from .views import load_email_settings
from .models import Contrat

@shared_task
def check_contracts():
    today = timezone.now().date()
    notify_date = today + timedelta(days=5)
    
    # Contrats arrivant à expiration dans 5 jours
    contracts_to_notify = Contrat.objects.filter(date_fin=notify_date, est_terminer=False)
    for contrat in contracts_to_notify:
        # Charger les paramètres d'email
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        # Envoyer un email de notification
        subject = 'Contrat arrivant à expiration'
        message = f'Salutation, le contrat du salarié {contrat.salarie.nom_salarie} {contrat.salarie.prenom_salarie} avec {contrat.entreprise.nom_entreprise} se termine le {contrat.date_fin}.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [contrat.salarie.compte.email, contrat.entreprise.compte.email]

        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
    # Contrats arrivant à expiration aujourd'hui
    contracts_to_terminate = Contrat.objects.filter(date_fin=today, est_terminer=False)
    for contrat in contracts_to_terminate:
        # Mettre à jour le statut
        contrat.est_terminer= True
        contrat.save()
        # Envoyer un email de notification
        email_settings = load_email_settings()
        if email_settings:
            settings.EMAIL_HOST = email_settings['EMAIL_HOST']
            settings.EMAIL_PORT = email_settings['EMAIL_PORT']
            settings.EMAIL_USE_TLS = email_settings['EMAIL_USE_TLS']
            settings.EMAIL_USE_SSL = email_settings['EMAIL_USE_SSL']
            settings.EMAIL_HOST_USER = email_settings['EMAIL_HOST_USER']
            settings.EMAIL_HOST_PASSWORD = email_settings['EMAIL_HOST_PASSWORD']
        # Envoyer un email de notification
        subject = 'Contrat terminé',
        message = f'Bonjour, le contrat du salarié {contrat.salarie.nom_salarie} {contrat.salarie.prenom_salarie} avec {contrat.entreprise.nom_entreprise} se termine aujourd\'hui.',
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [contrat.salarie.compte.email, contrat.entreprise.compte.email]

        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )