from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions are only allowed to the owner or admin users
        return obj == request.user or request.user.is_staff


class HasCustomPermission(permissions.BasePermission):
    """
    Custom permission to check if user has specific permission based on role or custom permissions.
    """
    
    def __init__(self, category=None, action_type=None):
        self.category = category
        self.action_type = action_type
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # If category and action_type are specified, check specific permission
        if self.category and self.action_type:
            return request.user.has_permission(self.category, self.action_type)
        
        return True
