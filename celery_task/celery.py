from __future__ import absolute_import
from celery import Celery

celery_app = Celery('tasks')
celery_app.config_from_object('celery_task.celeryconfig')
