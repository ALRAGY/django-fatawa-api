import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from accounts.models import User, Role, Permission, RolePermission, UserPermission
from accounts.serializers import RolePermissionSerializer

# 1. Clear test data
RolePermission.objects.filter(role_id=1, permission_id=10).delete()
UserPermission.objects.filter(permission_id=10).delete()

# 2. Get first role and permission 10 (or create it)
role = Role.objects.get(role_id=1)
perm, _ = Permission.objects.get_or_create(permission_id=10, defaults={'category': 'test', 'action_type': 'test'})

# 3. Get custom users
custom_users = list(User.objects.filter(role=role, is_custom=True))
print(f"Custom users with role 1: {[u.username for u in custom_users]}")

# 4. Create RolePermission via serializer just like via API
data = {'role_id': role.role_id, 'permission_id': perm.permission_id}
serializer = RolePermissionSerializer(data=data)
if serializer.is_valid():
    rp = serializer.save()
    
    # Run the exact code from perform_create
    custom_q = User.objects.filter(role=rp.role, is_custom=True)
    print(f"Custom users in perform_create: {custom_q.count()}")
    if custom_q.exists():
        user_perms = [UserPermission(user=cu, permission=rp.permission) for cu in custom_q]
        print(f"Creating user perms: {len(user_perms)}")
        UserPermission.objects.bulk_create(user_perms, ignore_conflicts=True)
        for cu in custom_q:
            print(f"Called sync for {cu.username}")

    # Verify if it was added to the custom users
    for cu in custom_users:
        has_perm = UserPermission.objects.filter(user=cu, permission=perm).exists()
        print(f"User {cu.username} has physically synced perm in UserPermission? {has_perm}")
else:
    print(serializer.errors)

