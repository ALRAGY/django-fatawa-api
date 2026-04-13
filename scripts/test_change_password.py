import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from rest_framework.test import APIClient
from accounts.models import User

# Setup User and Client
try:
    user = User.objects.get(username='test_pwd_user')
    user.set_password('OldPassword123!')
    user.save()
except User.DoesNotExist:
    user = User.objects.create_user(username='test_pwd_user', password='OldPassword123!', email='test_pwd@local.com')

client = APIClient(SERVER_NAME='localhost')
client.force_authenticate(user=user)

payload_fail = {
    "old_password": "WrongPassword123!",
    "new_password": "NewPassword123!"
}

payload_success = {
    "old_password": "OldPassword123!",
    "new_password": "NewPassword123!"
}

print("1. Testing with WRONG old password...")
res_fail = client.post('/api/auth/users/change-password/', payload_fail, format='json')
print(f"Status Code: {res_fail.status_code}")
print(f"Response: {res_fail.data}")

print("\n2. Testing with CORRECT old password...")
res_success = client.post('/api/auth/users/change-password/', payload_success, format='json')
print(f"Status Code: {res_success.status_code}")
print(f"Response: {res_success.data}")

# Clean up
user = User.objects.get(username='test_pwd_user')
print(f"\nCan login with new password? {user.check_password('NewPassword123!')}")
user.delete()
