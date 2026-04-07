from django.contrib import admin
from .models import User, Role, Permission, RolePermission, UserPermission


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['role_id', 'role_name', 'description']
    search_fields = ['role_name']
    ordering = ['role_name']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['permission_id', 'category', 'action_type', 'display_name_ar']
    list_filter = ['category', 'action_type']
    search_fields = ['category', 'action_type', 'display_name_ar']
    ordering = ['category', 'action_type']


class UserPermissionInline(admin.TabularInline):
    model = UserPermission
    extra = 1


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'username', 'email', 'role', 'is_custom', 'is_active', 'date_joined']
    list_filter = ['is_active', 'is_custom', 'role', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    inlines = [UserPermissionInline]
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'email', 'first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('role', 'is_custom', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission']
    list_filter = ['role', 'permission__category']
    search_fields = ['role__role_name', 'permission__category', 'permission__action_type']


@admin.register(UserPermission)
class UserPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission']
    list_filter = ['permission__category']
    search_fields = ['user__username', 'permission__category', 'permission__action_type']
