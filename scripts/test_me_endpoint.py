import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from rest_framework.test import APIClient
from accounts.models import User

# Get admin user to authenticate
admin_user = User.objects.get(username='admin')

# Setup API Client
client = APIClient(SERVER_NAME='localhost')
client.force_authenticate(user=admin_user)

print("Sending GET request to /api/auth/me/ ...")
response = client.get('/api/auth/me/', format='json')

print(f"Status Code: {response.status_code}")
if hasattr(response, 'data'):
    print(f"Response: {json.dumps(response.data, indent=2)}")
    if response.data.get('username') == 'admin':
        print("✅ SUCCESS: /api/auth/me/ endpoint returns correct correct user details!")
    else:
        print("❌ FAILED: Incorrect user details.")
else:
    print(f"Response Content: {response.content}")
