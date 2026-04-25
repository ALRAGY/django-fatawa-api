import os
import django
import json
import sys

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from shared_inbox.models import ConnectedChannel

# The token provided by the user
youtube_creds = {
    "access_token": "YOUR_ACCESS_TOKEN",
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
}

channel, created = ConnectedChannel.objects.get_or_create(
    platform_identifier='YOUTUBE',
    defaults={
        'name': 'قناة الفتاوى الرسمية (YouTube)',
        'credentials': youtube_creds,
        'is_active': True
    }
)

if not created:
    channel.credentials = youtube_creds
    channel.save()
    print("تم تحديث القناة الموجودة بالتوكن الجديد.")
else:
    print("تم إدخال القناة لأول مرة لقاعدة البيانات.")
