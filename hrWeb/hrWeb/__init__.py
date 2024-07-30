# myproject/__init__.py
from __future__ import absolute_import, unicode_literals

# Ce code garantit que Celery sera importé lorsque Django démarre afin que les tâches soient toujours prêtes
from .celery import app as celery_app

__all__ = ('celery_app',)