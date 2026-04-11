"""
Enhanced API views with permission synchronization capabilities.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.db import transaction
from django.utils import timezone
from .models import User, Role, Permission, RolePermission, UserPermission
from .serializers import (
    UserSerializer, RoleSerializer, PermissionSerializer,
    RolePermissionSerializer, UserPermissionSerializer, LoginSerializer,
    UserRegisterSerializer
)
from .permissions import IsOwnerOrAdmin
from .permission_sync import PermissionSyncManager
from .permission_bulk import BulkPermissionManager, PermissionAnalytics
import logging

logger = logging.getLogger(__name__)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def bulk_assign_permissions(self, request, pk=None):
        """Bulk assign permissions to a role."""
        permission_ids = request.data.get('permission_ids', [])
        
        if not permission_ids:
            return Response(
                {'error': 'permission_ids list is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assigned_count = BulkPermissionManager.bulk_assign_role_permissions(
                pk, permission_ids
            )
            return Response({
                'message': f'Successfully assigned {assigned_count} permissions to role',
                'assigned_count': assigned_count
            })
        except Exception as e:
            logger.error(f"Error in bulk role permission assignment: {e}")
            return Response(
                {'error': 'Failed to assign permissions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAdminUser])
    def bulk_remove_permissions(self, request, pk=None):
        """Bulk remove permissions from a role."""
        permission_ids = request.data.get('permission_ids', [])
        
        if not permission_ids:
            return Response(
                {'error': 'permission_ids list is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        
        try:
            removed_count = BulkPermissionManager.bulk_remove_role_permissions(
                pk, permission_ids
            )
            return Response({
                'message': f'Successfully removed {removed_count} permissions from role',
                'removed_count': removed_count
            })
        except Exception as e:
            logger.error(f"Error in bulk role permission removal: {e}")
            return Response(
                {'error': 'Failed to remove permissions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class RolePermissionViewSet(viewsets.ModelViewSet):
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class UserPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = UserPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return UserPermission.objects.all()
        return UserPermission.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure user is marked as custom when adding custom permissions and copy role perms
        user_id = serializer.validated_data.get('user_id')
        user = User.objects.get(user_id=user_id)
        if not user.is_custom:
            if user.role:
                role_perms = RolePermission.objects.filter(role=user.role).values_list('permission_id', flat=True)
                existing = UserPermission.objects.filter(user=user).values_list('permission_id', flat=True)
                perms_to_add = [
                    UserPermission(user=user, permission_id=pid)
                    for pid in set(role_perms) - set(existing)
                ]
                if perms_to_add:
                    UserPermission.objects.bulk_create(perms_to_add, batch_size=100)
            user.is_custom = True
            user.save(update_fields=['is_custom'])
        
        serializer.save()
        PermissionSyncManager.sync_user_permissions(user.user_id)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def bulk_assign(self, request):
        """Bulk assign custom permissions to current user."""
        permission_ids = request.data.get('permission_ids', [])
        
        if not permission_ids:
            return Response(
                {'error': 'permission_ids list is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assigned_count = BulkPermissionManager.bulk_assign_user_permissions(
                request.user.user_id, permission_ids
            )
            return Response({
                'message': f'Successfully assigned {assigned_count} custom permissions',
                'assigned_count': assigned_count
            })
        except Exception as e:
            logger.error(f"Error in bulk user permission assignment: {e}")
            return Response(
                {'error': 'Failed to assign permissions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAdminUser] # Only Admin can register new users
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsOwnerOrAdmin]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegisterSerializer
        return UserSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_permissions(self, request):
        """Get current user's permissions."""
        permissions = request.user.get_all_permissions()
        return Response({
            'permissions': permissions,
            'is_custom': request.user.is_custom,
            'role': request.user.role.role_name if request.user.role else None
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def invalidate_cache(self, request):
        """Manually invalidate permission cache."""
        request.user.invalidate_permission_cache()
        return Response({'message': 'Permission cache invalidated'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def grant_permission(self, request, pk=None):
        user = self.get_object()
        permission_id = request.data.get('permission_id')
        
        if not permission_id:
            return Response({'error': 'permission_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            permission = Permission.objects.get(permission_id=permission_id)
            
            # COPY LOGIC: Ensure custom users inherit their previous role's permissions physically
            if not user.is_custom:
                if user.role:
                    role_perms = RolePermission.objects.filter(role=user.role).values_list('permission_id', flat=True)
                    existing = UserPermission.objects.filter(user=user).values_list('permission_id', flat=True)
                    perms_to_add = [
                        UserPermission(user=user, permission_id=pid)
                        for pid in set(role_perms) - set(existing)
                    ]
                    if perms_to_add:
                        UserPermission.objects.bulk_create(perms_to_add, batch_size=100)
                user.is_custom = True
                user.save(update_fields=['is_custom'])
            
            user_permission, created = UserPermission.objects.get_or_create(
                user=user, permission=permission
            )
            
            if created:
                PermissionSyncManager.sync_user_permissions(user.user_id)
                return Response({'message': 'Permission granted successfully'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Permission already exists'}, status=status.HTTP_200_OK)
                
        except Permission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAdminUser])
    def revoke_permission(self, request, pk=None):
        user = self.get_object()
        permission_id = request.data.get('permission_id')
        
        if not permission_id:
            return Response({'error': 'permission_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            permission = Permission.objects.get(permission_id=permission_id)
            user_permission = UserPermission.objects.filter(user=user, permission=permission).first()
            
            if user_permission:
                user_permission.delete()
                return Response({'message': 'Permission revoked successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Permission not found for this user'}, status=status.HTTP_404_NOT_FOUND)
                
        except Permission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=status.HTTP_404_NOT_FOUND)


class SystemManagementViewSet(viewsets.GenericViewSet):
    """
    System management endpoints for permission synchronization and analytics.
    """
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['post'])
    def sync_all_permissions(self, request):
        """Force sync all permissions in the system."""
        try:
            BulkPermissionManager.bulk_sync_all_permissions()
            return Response({'message': 'All permissions synchronized successfully'})
        except Exception as e:
            logger.error(f"Error in system-wide permission sync: {e}")
            return Response(
                {'error': 'Failed to synchronize permissions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def permission_analytics(self, request):
        """Get comprehensive permission analytics."""
        try:
            stats = PermissionAnalytics.get_permission_statistics()
            conflicts = PermissionAnalytics.identify_permission_conflicts()
            
            return Response({
                'statistics': stats,
                'conflicts': conflicts,
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error generating permission analytics: {e}")
            return Response(
                {'error': 'Failed to generate analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
