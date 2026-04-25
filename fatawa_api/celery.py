import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')

app = Celery('fatawa_api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'poll_all_channels_every_5_minutes': {
        'task': 'shared_inbox.tasks.fetch_all_polling_channels',
        'schedule': crontab(minute='*/5'),
    },
}
