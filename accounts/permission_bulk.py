"""
Advanced permission management utilities for bulk operations and performance optimization.
"""

from django.db import transaction, models
from django.core.cache import cache
from django.contrib.auth import get_user_model
from .models import Role, Permission, RolePermission, UserPermission
from .permission_sync import PermissionSyncManager
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class BulkPermissionManager:
    """
    High-performance bulk permission operations for large-scale environments.
    """
    
    @staticmethod
    @transaction.atomic
    def bulk_assign_role_permissions(role_id, permission_ids):
        """
        Bulk assign permissions to a role with optimized database operations.
        """
        try:
            role = Role.objects.get(role_id=role_id)
            
            # Get existing permissions to avoid duplicates
            existing_perms = RolePermission.objects.filter(
                role_id=role_id
            ).values_list('permission_id', flat=True)
            
            # Create only new permissions
            new_perms = [
                RolePermission(role=role, permission_id=perm_id)
                for perm_id in permission_ids
                if perm_id not in existing_perms
            ]
            
            if new_perms:
                RolePermission.objects.bulk_create(new_perms, batch_size=100)
                logger.info(f"Bulk assigned {len(new_perms)} permissions to role {role.role_name}")
                
                # Sync to all standard users in role
                PermissionSyncManager.sync_role_permissions_to_users(role_id)
                
                # Sync new permissions to custom users inheriting this role
                custom_users = User.objects.filter(role_id=role_id, is_custom=True)
                if custom_users.exists() and permission_ids:
                    user_perms_to_create = []
                    existing_user_perms = set(UserPermission.objects.filter(
                        user__in=custom_users, permission_id__in=permission_ids
                    ).values_list('user_id', 'permission_id'))
                    
                    for cu in custom_users:
                        for pid in permission_ids:
                            if (cu.user_id, pid) not in existing_user_perms:
                                user_perms_to_create.append(UserPermission(user=cu, permission_id=pid))
                    
                    if user_perms_to_create:
                        UserPermission.objects.bulk_create(user_perms_to_create, batch_size=500)
                        for cu in custom_users:
                            PermissionSyncManager.sync_user_permissions(cu.user_id)
            
            return len(new_perms)
            
        except Exception as e:
            logger.error(f"Error in bulk role permission assignment: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def bulk_assign_user_permissions(user_id, permission_ids):
        """
        Bulk assign custom permissions to a user.
        """
        try:
            user = User.objects.get(user_id=user_id)
            
            # Ensure user is marked as custom and copy existing role permissions
            if not user.is_custom:
                if user.role:
                    role_perms = RolePermission.objects.filter(role=user.role).values_list('permission_id', flat=True)
                    existing_up = UserPermission.objects.filter(user=user).values_list('permission_id', flat=True)
                    perms_to_add = [
                        UserPermission(user=user, permission_id=pid)
                        for pid in set(role_perms) - set(existing_up)
                    ]
                    if perms_to_add:
                        UserPermission.objects.bulk_create(perms_to_add, batch_size=100)
                
                user.is_custom = True
                user.save(update_fields=['is_custom'])
            
            # Get existing permissions
            existing_perms = UserPermission.objects.filter(
                user_id=user_id
            ).values_list('permission_id', flat=True)
            
            # Create only new permissions
            new_perms = [
                UserPermission(user=user, permission_id=perm_id)
                for perm_id in permission_ids
                if perm_id not in existing_perms
            ]
            
            if new_perms:
                UserPermission.objects.bulk_create(new_perms, batch_size=100)
                logger.info(f"Bulk assigned {len(new_perms)} custom permissions to user {user.username}")
                
                # Sync user permissions
                PermissionSyncManager.sync_user_permissions(user_id)
            
            return len(new_perms)
            
        except Exception as e:
            logger.error(f"Error in bulk user permission assignment: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def bulk_remove_role_permissions(role_id, permission_ids):
        """
        Bulk remove permissions from a role.
        """
        try:
            # Sync removal to custom users sharing this role before deleting the root
            custom_users = User.objects.filter(role_id=role_id, is_custom=True)
            if custom_users.exists() and permission_ids:
                deleted_custom = UserPermission.objects.filter(
                    user__in=custom_users, permission_id__in=permission_ids
                ).delete()[0]
                if deleted_custom > 0:
                    for cu in custom_users:
                        PermissionSyncManager.sync_user_permissions(cu.user_id)

            deleted_count = RolePermission.objects.filter(
                role_id=role_id,
                permission_id__in=permission_ids
            ).delete()[0]
            
            if deleted_count > 0:
                logger.info(f"Bulk removed {deleted_count} permissions from role {role_id}")
                PermissionSyncManager.sync_role_permissions_to_users(role_id)
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error in bulk role permission removal: {e}")
            raise
    
    @staticmethod
    @transaction.atomic
    def bulk_remove_user_permissions(user_id, permission_ids):
        """
        Bulk remove custom permissions from a user.
        """
        try:
            deleted_count = UserPermission.objects.filter(
                user_id=user_id,
                permission_id__in=permission_ids
            ).delete()[0]
            
            if deleted_count > 0:
                logger.info(f"Bulk removed {deleted_count} custom permissions from user {user_id}")
                PermissionSyncManager.sync_user_permissions(user_id)
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error in bulk user permission removal: {e}")
            raise
    
    @staticmethod
    def bulk_sync_all_permissions():
        """
        Sync permissions for all users - useful for system maintenance.
        """
        logger.info("Starting bulk permission synchronization for all users")
        
        try:
            # Clear all permission caches
            cache.delete_many([
                PermissionSyncManager.get_user_cache_key(user.user_id)
                for user in User.objects.all()
            ])
            
            # Sync by roles for efficiency
            for role in Role.objects.all():
                PermissionSyncManager.sync_role_permissions_to_users(role.role_id)
            
            # Sync custom permission users
            custom_users = User.objects.filter(is_custom=True)
            for user in custom_users:
                PermissionSyncManager.sync_user_permissions(user.user_id)
            
            logger.info("Bulk permission synchronization completed")
            
        except Exception as e:
            logger.error(f"Error in bulk permission sync: {e}")
            raise


class PermissionAnalytics:
    """
    Analytics and reporting for permission management.
    """
    
    @staticmethod
    def get_permission_statistics():
        """
        Get comprehensive permission statistics.
        """
        stats = {
            'total_users': User.objects.count(),
            'custom_users': User.objects.filter(is_custom=True).count(),
            'role_based_users': User.objects.filter(is_custom=False, role__isnull=False).count(),
            'total_roles': Role.objects.count(),
            'total_permissions': Permission.objects.count(),
            'role_permissions': RolePermission.objects.count(),
            'user_permissions': UserPermission.objects.count(),
        }
        
        # Permission distribution by category
        stats['permission_categories'] = dict(
            Permission.objects.values_list('category')
            .annotate(count=models.Count('permission_id'))
            .values_list('category', 'count')
        )
        
        # Role distribution
        stats['role_distribution'] = dict(
            User.objects.values('role__role_name')
            .annotate(count=models.Count('user_id'))
            .values_list('role__role_name', 'count')
        )
        
        return stats
    
    @staticmethod
    def identify_permission_conflicts():
        """
        Identify potential permission conflicts or inconsistencies.
        """
        conflicts = []
        
        # Users with both role-based and custom permissions
        mixed_users = User.objects.filter(
            is_custom=False,
            role__isnull=False
        ).filter(
            user_permissions__isnull=False
        ).distinct()
        
        if mixed_users.exists():
            conflicts.append({
                'type': 'mixed_permission_users',
                'users': list(mixed_users.values_list('username', flat=True)),
                'message': 'Users have both role-based and custom permissions'
            })
        
        # Roles with no permissions
        empty_roles = Role.objects.annotate(
            perm_count=models.Count('role_permissions')
        ).filter(perm_count=0)
        
        if empty_roles.exists():
            conflicts.append({
                'type': 'empty_roles',
                'roles': list(empty_roles.values_list('role_name', flat=True)),
                'message': 'Roles have no permissions assigned'
            })
        
        return conflicts
