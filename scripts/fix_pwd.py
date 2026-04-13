import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from accounts.models import User

user = User.objects.get(username='alragy')
user.set_password('alragy1234')
user.save()
print("Fixed alragy password.")
