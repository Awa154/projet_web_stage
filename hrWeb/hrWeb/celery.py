# myproject/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Définir les paramètres de Django pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrWeb.settings')

app = Celery('hrWeb')

# Charger les paramètres de configuration à partir des paramètres Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches asynchrones définies dans les applications Django
app.autodiscover_tasks()
