import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from accounts.models import User

try:
    user = User.objects.get(username='alragy')
    print(f"alragy exists.")
    print(f"Password hash strictly stored: {user.password}")
    print(f"Has usable password: {user.has_usable_password()}")
except User.DoesNotExist:
    print("User alragy not found.")
