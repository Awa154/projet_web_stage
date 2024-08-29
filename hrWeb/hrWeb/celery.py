from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Définissez le module de configuration par défaut de Django pour 'celery'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrWeb.settings')

app = Celery('hrWeb')

# Charger les configurations à partir du fichier settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger les tâches des applications installées
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
