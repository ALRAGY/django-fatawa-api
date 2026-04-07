from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .enhanced_views import (
    UserViewSet, RoleViewSet, PermissionViewSet,
    RolePermissionViewSet, UserPermissionViewSet, SystemManagementViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permission')
router.register(r'user-permissions', UserPermissionViewSet, basename='user-permission')
router.register(r'system', SystemManagementViewSet, basename='system')

urlpatterns = [
    path('', include(router.urls)),
]
