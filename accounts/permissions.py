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


class HasAccess(permissions.BasePermission):
    """
    مراقب الصلاحيات الذكي: يقرأ متغير `required_permission` مباشرة 
    من الـ View أو الـ ViewSet ويتحقق من صلاحية المستخدم ديناميكياً.
    """
    
    def has_permission(self, request, view):
        # 1. Check if authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 2. Get the required permission from the View
        # e.g., required_permission = "qustion.add"
        required_perm = getattr(view, 'required_permission', None)
        
        # Security first: If the view developer forgot to define required_permission, deny access.
        if not required_perm:
            return False
            
        # 3. Parse "category.action_type"
        try:
            category, action_type = required_perm.split('.')
            # Call our robust has_permission method from User model
            return request.user.has_permission(category, action_type)
        except ValueError:
            # Malformed required_permission string (e.g. missing dot)
            return False
