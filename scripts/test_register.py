import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from rest_framework.test import APIClient
from accounts.models import User
import json

# 1. Clean up test user if exists
User.objects.filter(username='test_user_99').delete()

# 2. Get admin user to authenticate
admin_user = User.objects.get(username='admin')

# 3. Setup API Client
client = APIClient(SERVER_NAME='localhost')
client.force_authenticate(user=admin_user)

# 4. Payload for new user
payload = {
    "username": "test_user_99",
    "password": "StrongPassword123!",
    "email": "test@fatawa.local",
    "first_name": "Test",
    "last_name": "User",
}

# 5. POST to create
print("Sending POST request to /api/auth/users/ ...")
response = client.post('/api/auth/users/', payload, format='json')

print(f"Status Code: {response.status_code}")
if hasattr(response, 'data'):
    print(f"Response: {json.dumps(response.data, indent=2)}")
else:
    print(f"Response Content: {response.content}")

# 6. Verify password hashing
if response.status_code == 201:
    created_user = User.objects.get(username='test_user_99')
    # Check if the DB password is plain text
    is_plain_text = (created_user.password == 'StrongPassword123!')
    is_correct_hash = created_user.check_password('StrongPassword123!')
    
    print("\n--- Validation ---")
    print(f"Is Password Stored in Plain Text? {is_plain_text}")
    print(f"Is Password Hashed Correctly? {is_correct_hash}")
    
    if not is_plain_text and is_correct_hash:
        print("✅ SUCCESS: Registration API works flawlessly with password hashing!")
    else:
        print("❌ FAILED: Password hashing issue.")
else:
    print("❌ FAILED: API rejected the request.")

# Cleanup
created_user.delete()
