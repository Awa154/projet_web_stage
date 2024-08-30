from django.db.models import Count
from .models import *
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



def sidebar_context(request):
    # Comptage des demandes par statut
    demandes_en_attente = Demande.objects.filter(statut='EN_ATTENTE').count()
    demandes_validees = Demande.objects.filter(statut='VALIDE').count()
    demandes_refusees = Demande.objects.filter(statut='REFUSE').count()

    context = {
        'demandes_en_attente': demandes_en_attente,
        'demandes_validees': demandes_validees,
        'demandes_refusees': demandes_refusees,
    }
    return context

def sidebar_utilisateur(request):
    if not hasattr(request.user, 'id'):
        messages.error(request, "Vous devez être connecté pour accéder à cette page.")
        return redirect('connexion')

    user = request.user

    user_demandes_en_attente = Demande.objects.filter(compte=user, statut='EN_ATTENTE').count()
    user_demandes_validees = Demande.objects.filter(compte=user, statut='VALIDE').count()
    user_demandes_refusees = Demande.objects.filter(compte=user, statut='REFUSE').count()

    context_utilisateur = {
        'user_demandes_en_attente': user_demandes_en_attente,
        'user_demandes_validees': user_demandes_validees,
        'user_demandes_refusees': user_demandes_refusees,
    }
    return context_utilisateur

