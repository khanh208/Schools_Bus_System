# config/celery.py
from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

# Set default Django settings module cho Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Đọc config từ Django settings, với prefix "CELERY_"
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động tìm tasks.py trong các app đã cài
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
