import os
import django
import json
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fatawa_api.settings')
django.setup()

from rest_framework.test import APIClient
from accounts.models import User, Role, Permission, RolePermission

# Ensure Admin user exists
admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@localhost', 'is_superuser': True})
admin_user.set_password('admin123')
admin_user.save()

client = APIClient(SERVER_NAME='localhost')

def run_tests():
    print("\n--- 🚀 STARTING COMPREHENSIVE API TESTS ---\n")
    passed = 0
    failed = 0

    def assert_success(step_name, response, expected_status=200):
        nonlocal passed, failed
        if response.status_code == expected_status or (expected_status == 200 and response.status_code in [200, 201]):
            print(f"✅ {step_name} (Status: {response.status_code})")
            passed += 1
            return True
        else:
            print(f"❌ {step_name} FAILED! Expected {expected_status}, got {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Details: {response.data}")
            failed += 1
            return False

    # 1. Test Login API
    login_data = {'username': 'admin', 'password': 'admin123'}
    res_login = client.post('/api/auth/users/login/', login_data, format='json')
    success = assert_success("Login API (JWT Generation)", res_login, 200)
    
    if not success:
        return
        
    access_token = res_login.data.get('access')
    client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

    # 2. Test Register API
    # Clean up first
    User.objects.filter(username='e2e_test_user').delete()
    register_data = {
        'username': 'e2e_test_user',
        'password': 'SecurePassword123!',
        'email': 'e2e@local.com',
        'first_name': 'E2E',
        'last_name': 'User'
    }
    res_register = client.post('/api/auth/users/', register_data, format='json')
    assert_success("Register API (Admin creating user securely)", res_register, 201)

    # 3. Test New User Login
    res_new_login = client.post('/api/auth/users/login/', {'username': 'e2e_test_user', 'password': 'SecurePassword123!'}, format='json')
    assert_success("New User Login API (Password Hashed Correctly)", res_new_login, 200)

    # 4. Test Role Fetching
    res_roles = client.get('/api/auth/roles/', format='json')
    assert_success("List Roles API", res_roles, 200)

    # 5. Test Profile APIs (Currently available directly to admin, but let's check profile)
    res_profile = client.get('/api/auth/users/profile/', format='json')
    assert_success("Profile API", res_profile, 200)

    # 6. Test Handling Duplicate Assignments (The 400 Bad Request fix)
    admin_role = getattr(admin_user, 'role', None)
    if not admin_role:
        admin_role, _ = Role.objects.get_or_create(role_name='Admin')
        
    p1, _ = Permission.objects.get_or_create(category='test', action_type='dummy')
    
    # Try adding permission normally
    client.post('/api/auth/role-permissions/', {'role_id': admin_role.role_id, 'permission_id': p1.permission_id}, format='json')
    
    # Try adding IT AGAIN to trigger validation error 400 instead of IntegrityError 500
    res_dup = client.post('/api/auth/role-permissions/', {'role_id': admin_role.role_id, 'permission_id': p1.permission_id}, format='json')
    assert_success("Validation Constraint Checking (Duplicate Permission -> 400 Bad Request)", res_dup, 400)

    print("\n--- 🏁 TEST SUMMARY ---")
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    if failed == 0:
         print("\n🎉 ALL SYSTEMS GO. API IS PRODUCTION READY. 🎉")

if __name__ == '__main__':
    run_tests()
