"""
Test cases for permission synchronization system.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Role, Permission, RolePermission, UserPermission
from .permission_sync import PermissionSyncManager
from .permission_bulk import BulkPermissionManager, PermissionAnalytics

User = get_user_model()


class PermissionSyncTestCase(TestCase):
    """Test permission synchronization functionality."""
    
    def setUp(self):
        """Set up test data."""
        cache.clear()
        
        # Create test role
        self.role = Role.objects.create(
            role_name='TestRole',
            description='Test role description'
        )
        
        # Create test permissions
        self.perm1 = Permission.objects.create(
            category='TEST',
            action_type='CREATE',
            display_name_ar='إنشاء اختبار'
        )
        self.perm2 = Permission.objects.create(
            category='TEST',
            action_type='DELETE',
            display_name_ar='حذف اختبار'
        )
        
        # Create test user with role
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.role = self.role
        self.user.save()
        
        # Create custom user
        self.custom_user = User.objects.create_user(
            username='customuser',
            email='custom@example.com',
            password='testpass123',
            is_custom=True
        )
    
    def test_role_permission_sync_on_creation(self):
        """Test that role permission creation syncs to users."""
        # Assign permission to role
        RolePermission.objects.create(
            role=self.role,
            permission=self.perm1
        )
        
        # Check if user has the permission
        self.assertTrue(
            self.user.has_permission('TEST', 'CREATE'),
            "User should have permission from role"
        )
        
        # Check cache is working
        permissions = PermissionSyncManager.get_user_permissions(self.user.user_id)
        self.assertIn('TEST.CREATE', permissions)
    
    def test_custom_permission_sync_on_creation(self):
        """Test that custom permission creation syncs immediately."""
        # Assign custom permission
        UserPermission.objects.create(
            user=self.custom_user,
            permission=self.perm2
        )
        
        # Check if custom user has the permission
        self.assertTrue(
            self.custom_user.has_permission('TEST', 'DELETE'),
            "Custom user should have direct permission"
        )
    
    def test_permission_cache_invalidation(self):
        """Test permission cache invalidation."""
        # Create initial permission
        RolePermission.objects.create(
            role=self.role,
            permission=self.perm1
        )
        
        # Get cached permissions
        permissions1 = PermissionSyncManager.get_user_permissions(self.user.user_id)
        self.assertIn('TEST.CREATE', permissions1)
        
        # Add new permission
        RolePermission.objects.create(
            role=self.role,
            permission=self.perm2
        )
        
        # Cache should be invalidated
        permissions2 = PermissionSyncManager.get_user_permissions(self.user.user_id)
        self.assertIn('TEST.DELETE', permissions2)
    
    def test_bulk_role_permission_assignment(self):
        """Test bulk permission assignment to role."""
        permission_ids = [self.perm1.permission_id, self.perm2.permission_id]
        
        assigned_count = BulkPermissionManager.bulk_assign_role_permissions(
            self.role.role_id, permission_ids
        )
        
        self.assertEqual(assigned_count, 2)
        self.assertTrue(self.user.has_permission('TEST', 'CREATE'))
        self.assertTrue(self.user.has_permission('TEST', 'DELETE'))
    
    def test_bulk_user_permission_assignment(self):
        """Test bulk permission assignment to user."""
        permission_ids = [self.perm1.permission_id, self.perm2.permission_id]
        
        assigned_count = BulkPermissionManager.bulk_assign_user_permissions(
            self.custom_user.user_id, permission_ids
        )
        
        self.assertEqual(assigned_count, 2)
        self.assertTrue(self.custom_user.has_permission('TEST', 'CREATE'))
        self.assertTrue(self.custom_user.has_permission('TEST', 'DELETE'))
        self.assertTrue(self.custom_user.is_custom)
    
    def test_permission_analytics(self):
        """Test permission analytics functionality."""
        # Create some test data
        RolePermission.objects.create(role=self.role, permission=self.perm1)
        UserPermission.objects.create(user=self.custom_user, permission=self.perm2)
        
        stats = PermissionAnalytics.get_permission_statistics()
        
        self.assertGreater(stats['total_users'], 0)
        self.assertGreater(stats['total_roles'], 0)
        self.assertGreater(stats['total_permissions'], 0)
        self.assertIn('TEST', stats['permission_categories'])
    
    def test_permission_conflict_detection(self):
        """Test permission conflict detection."""
        # Create a user with both role and custom permissions
        mixed_user = User.objects.create_user(
            username='mixeduser',
            email='mixed@example.com',
            password='testpass123',
            is_custom=False
        )
        mixed_user.role = self.role
        mixed_user.save()
        
        # Add role permission
        RolePermission.objects.create(role=self.role, permission=self.perm1)
        
        # Add custom permission (this creates a conflict)
        UserPermission.objects.create(user=mixed_user, permission=self.perm2)
        
        conflicts = PermissionAnalytics.identify_permission_conflicts()
        
        # Should detect the mixed permission user
        mixed_conflicts = [c for c in conflicts if c['type'] == 'mixed_permission_users']
        self.assertTrue(len(mixed_conflicts) > 0)


class PermissionAPITestCase(APITestCase):
    """Test permission API endpoints."""
    
    def setUp(self):
        """Set up API test data."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.role = Role.objects.create(
            role_name='APIRole',
            description='API test role'
        )
        
        self.permission = Permission.objects.create(
            category='API',
            action_type='TEST',
            display_name_ar='اختبار API'
        )
    
    def test_bulk_role_permission_assignment_api(self):
        """Test bulk role permission assignment via API."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'permission_ids': [self.permission.permission_id]
        }
        
        response = self.client.post(
            f'/api/auth/roles/{self.role.role_id}/bulk_assign_permissions/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('assigned_count', response.data)
    
    def test_permission_analytics_api(self):
        """Test permission analytics API endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/auth/system/permission_analytics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('statistics', response.data)
        self.assertIn('conflicts', response.data)
    
    def test_user_permissions_api(self):
        """Test user permissions endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/api/auth/users/my_permissions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('permissions', response.data)
        self.assertIn('is_custom', response.data)
