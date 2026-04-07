"""
Permission synchronization system for robust user access control.

This module provides automatic permission synchronization between roles and users,
ensuring data integrity and performance optimization through caching and bulk operations.
"""

from django.db import models, transaction
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class PermissionSyncManager:
    """
    Centralized permission synchronization manager with caching and bulk operations.
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = 'user_permissions'
    
    @classmethod
    def get_user_cache_key(cls, user_id):
        """Generate cache key for user permissions."""
        return f"{cls.CACHE_KEY_PREFIX}_{user_id}"
    
    @classmethod
    def invalidate_user_cache(cls, user_id):
        """Invalidate permission cache for a specific user."""
        cache_key = cls.get_user_cache_key(user_id)
        cache.delete(cache_key)
    
    @classmethod
    def invalidate_role_cache(cls, role_id):
        """Invalidate permission cache for all users in a role."""
        User = get_user_model()
        users = User.objects.filter(role_id=role_id).values_list('user_id', flat=True)
        for user_id in users:
            cls.invalidate_user_cache(user_id)
    
    @classmethod
    def get_user_permissions(cls, user_id):
        """Get user permissions with caching."""
        # Handle invalid user_id (for anonymous users)
        if not user_id:
            return []
            
        cache_key = cls.get_user_cache_key(user_id)
        permissions = cache.get(cache_key)
        
        if permissions is None:
            permissions = cls._compute_user_permissions(user_id)
            cache.set(cache_key, permissions, cls.CACHE_TIMEOUT)
        
        return permissions
    
    @classmethod
    def _compute_user_permissions(cls, user_id):
        """Compute actual permissions for a user."""
        User = get_user_model()
        try:
            user = User.objects.select_related('role').get(user_id=user_id)
            
            if user.is_superuser:
                return 'ALL_PERMISSIONS'
            
            if user.is_custom:
                # Custom permissions
                user_perms = UserPermission.objects.filter(
                    user=user
                ).select_related('permission')
                return {
                    f"{perm.permission.category}.{perm.permission.action_type}"
                    for perm in user_perms
                }
            else:
                # Role-based permissions
                if user.role:
                    role_perms = RolePermission.objects.filter(
                        role=user.role
                    ).select_related('permission')
                    return {
                        f"{perm.permission.category}.{perm.permission.action_type}"
                        for perm in role_perms
                    }
                return set()
                
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found during permission computation")
            return set()
    
    @classmethod
    @transaction.atomic
    def sync_role_permissions_to_users(cls, role_id):
        """
        Synchronize role permissions to all users in that role.
        This is called when role permissions are modified.
        """
        User = get_user_model()
        try:
            role = Role.objects.select_related().get(role_id=role_id)
            users = User.objects.filter(role=role, is_custom=False)
            
            logger.info(f"Syncing permissions for role {role.role_name} to {users.count()} users")
            
            # Invalidate cache for all affected users
            cls.invalidate_role_cache(role_id)
            
            # Log synchronization
            for user in users:
                logger.info(f"Invalidated cache for user {user.username} due to role permission change")
                
        except Role.DoesNotExist:
            logger.error(f"Role {role_id} not found during permission sync")
    
    @classmethod
    @transaction.atomic
    def sync_user_permissions(cls, user_id):
        """
        Synchronize permissions for a specific user.
        This is called when user permissions are modified or user role changes.
        """
        User = get_user_model()
        try:
            user = User.objects.select_related('role').get(user_id=user_id)
            
            # Invalidate cache
            cls.invalidate_user_cache(user_id)
            
            logger.info(f"Synced permissions for user {user.username}")
            
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found during permission sync")
    
    @classmethod
    def bulk_sync_permissions(cls, user_ids=None, role_ids=None):
        """
        Bulk permission synchronization for performance optimization.
        """
        with transaction.atomic():
            if role_ids:
                for role_id in role_ids:
                    cls.sync_role_permissions_to_users(role_id)
            
            if user_ids:
                for user_id in user_ids:
                    cls.sync_user_permissions(user_id)


@receiver(post_save, sender='accounts.RolePermission')
def role_permission_created(sender, instance, created, **kwargs):
    """Handle role permission creation."""
    if created:
        logger.info(f"Role permission created: {instance.role.role_name} - {instance.permission.category}.{instance.permission.action_type}")
        PermissionSyncManager.sync_role_permissions_to_users(instance.role.role_id)


@receiver(post_delete, sender='accounts.RolePermission')
def role_permission_deleted(sender, instance, **kwargs):
    """Handle role permission deletion."""
    logger.info(f"Role permission deleted: {instance.role.role_name} - {instance.permission.category}.{instance.permission.action_type}")
    PermissionSyncManager.sync_role_permissions_to_users(instance.role.role_id)


@receiver(post_save, sender='accounts.UserPermission')
def user_permission_created(sender, instance, created, **kwargs):
    """Handle user permission creation."""
    if created:
        logger.info(f"User permission created: {instance.user.username} - {instance.permission.category}.{instance.permission.action_type}")
        PermissionSyncManager.sync_user_permissions(instance.user.user_id)


@receiver(post_delete, sender='accounts.UserPermission')
def user_permission_deleted(sender, instance, **kwargs):
    """Handle user permission deletion."""
    logger.info(f"User permission deleted: {instance.user.username} - {instance.permission.category}.{instance.permission.action_type}")
    PermissionSyncManager.sync_user_permissions(instance.user.user_id)


@receiver(post_save, sender='accounts.User')
def user_updated(sender, instance, created, **kwargs):
    """Handle user updates, especially role changes."""
    if not created:
        User = get_user_model()
        # Check if role changed
        try:
            old_user = User.objects.get(user_id=instance.user_id)
            if old_user.role_id != instance.role_id or old_user.is_custom != instance.is_custom:
                logger.info(f"User {instance.username} role or custom status changed")
                PermissionSyncManager.sync_user_permissions(instance.user_id)
        except User.DoesNotExist:
            pass
