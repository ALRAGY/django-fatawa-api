from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role, Permission, RolePermission, UserPermission


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'role_name', 'description']


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['permission_id', 'category', 'action_type', 'display_name_ar']


class RolePermissionSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    permission = PermissionSerializer(read_only=True)
    role_id = serializers.IntegerField(write_only=True)
    permission_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = RolePermission
        fields = ['role', 'permission', 'role_id', 'permission_id']

    def validate(self, data):
        role_id = data.get('role_id')
        permission_id = data.get('permission_id')
        if RolePermission.objects.filter(role_id=role_id, permission_id=permission_id).exists():
            raise serializers.ValidationError(
                {"detail": "This permission has already been assigned to this role."}
            )
        return data


class UserPermissionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    permission = PermissionSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    permission_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserPermission
        fields = ['user', 'permission', 'user_id', 'permission_id']

    def validate(self, data):
        user_id = data.get('user_id')
        permission_id = data.get('permission_id')
        if UserPermission.objects.filter(user_id=user_id, permission_id=permission_id).exists():
            raise serializers.ValidationError(
                {"detail": "This permission has already been assigned to this user."}
            )
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 'password', 'role_id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        role_id = validated_data.pop('role_id', None)
        
        user = User(**validated_data)
        user.set_password(password)  # Securely hash the password
        
        if role_id:
            user.role_id = role_id
            
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'role_id', 'is_custom', 'is_active', 'date_joined', 'permissions']
        read_only_fields = ['user_id', 'date_joined']
    
    def get_permissions(self, obj):
        # Handle anonymous users
        if not obj.is_authenticated:
            return []
            
        if obj.is_custom:
            permissions = UserPermission.objects.filter(user=obj)
            return UserPermissionSerializer(permissions, many=True).data
        else:
            if obj.role:
                permissions = RolePermission.objects.filter(role=obj.role)
                return RolePermissionSerializer(permissions, many=True).data
            return []
    
    def create(self, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)
        
        user = User.objects.create_user(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        if role_id:
            try:
                role = Role.objects.get(role_id=role_id)
                user.role = role
                user.save()
            except Role.DoesNotExist:
                pass
        
        return user
    
    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        if role_id is not None:
            try:
                role = Role.objects.get(role_id=role_id)
                instance.role = role
            except Role.DoesNotExist:
                instance.role = None
        
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            data['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Invalid old password.")
        return value
