import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from accounts.models import User, Role, Permission, RolePermission

print("Starting Admin Setup...")

# 1. Create or get Admin Role
admin_role, _ = Role.objects.get_or_create(
    role_name='Admin', 
    defaults={'description': 'Full System Administrator'}
)

# 2. Assign all permissions in the system to the Admin Role
all_permissions = list(Permission.objects.all())
existing_role_perms = set(RolePermission.objects.filter(role=admin_role).values_list('permission_id', flat=True))

perms_to_add = [
    RolePermission(role=admin_role, permission=p) 
    for p in all_permissions 
    if p.permission_id not in existing_role_perms
]

if perms_to_add:
    RolePermission.objects.bulk_create(perms_to_add, ignore_conflicts=True)
    print(f"Added {len(perms_to_add)} permissions to Admin role.")
else:
    print("Admin role already has all permissions.")

# 3. Handle 'admin' User
try:
    admin_user = User.objects.get(username='admin')
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.is_active = True
    admin_user.role = admin_role
    admin_user.set_password('admin123')
    admin_user.save()
    print("Updated existing 'admin' user (Password: admin123).")
except User.DoesNotExist:
    admin_user = User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    admin_user.role = admin_role
    admin_user.save()
    print("Created new 'admin' user (Password: admin123).")

# 4. Delete everyone else
other_users = User.objects.exclude(username='admin')
count = other_users.count()
if count > 0:
    for u in other_users:
        print(f"Deleting user: {u.username}")
    other_users.delete()
    print(f"Successfully deleted {count} other users.")
else:
    print("No other users found.")

print("Done! Admin setup complete.")
