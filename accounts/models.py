from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.cache import cache
import uuid
from .permission_sync import PermissionSyncManager


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True, verbose_name="Role Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.role_name


class Permission(models.Model):
    permission_id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=50, verbose_name="Category") 
    action_type = models.CharField(max_length=20, verbose_name="Action Type")  
    display_name_ar = models.CharField(max_length=100, blank=True, null=True, verbose_name="Display Name (AR)")
    
    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        unique_together = ('category', 'action_type')
    
    def __str__(self):
        return f"{self.category}.{self.action_type}"


class User(AbstractUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True, verbose_name="Username")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, 
                           related_name='users', verbose_name="Role")
    is_custom = models.BooleanField(default=False, verbose_name="Is Custom")  
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username
    
    @property
    def has_custom_permissions(self):
        """Check if user has custom permissions"""
        return self.is_custom
    
    def has_permission(self, category, action_type):
        """Check if user has specific permission with caching for performance"""
        # Handle anonymous users
        if not self.is_authenticated:
            return False
            
        if self.is_superuser:
            return True
        
        # Get cached permissions
        permissions = PermissionSyncManager.get_user_permissions(self.user_id)
        
        if permissions == 'ALL_PERMISSIONS':
            return True
        
        permission_key = f"{category}.{action_type}"
        return permission_key in permissions
    
    def get_all_permissions(self):
        """Get all permissions for this user"""
        # Handle anonymous users
        if not self.is_authenticated:
            return []
            
        permissions = PermissionSyncManager.get_user_permissions(self.user_id)
        
        if permissions == 'ALL_PERMISSIONS':
            return ['ALL_PERMISSIONS']
        
        return list(permissions)
    
    def invalidate_permission_cache(self):
        """Invalidate permission cache for this user"""
        if self.is_authenticated:
            PermissionSyncManager.invalidate_user_cache(self.user_id)


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ('role', 'permission')
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
    
    def __str__(self):
        return f"{self.role.role_name} - {self.permission.category}.{self.permission.action_type}"


class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_user_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='user_permissions')
    
    class Meta:
        db_table = 'user_permissions'
        unique_together = ('user', 'permission')
        verbose_name = 'User Permission'
        verbose_name_plural = 'User Permissions'
    
    def __str__(self):
        return f"{self.user.username} - {self.permission.category}.{self.permission.action_type}"
