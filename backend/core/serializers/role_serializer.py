from rest_framework import serializers

from django.contrib.auth.models import Permission

from core.models import Role
from core.permission_codes import permission_code, permission_identity


class PermissionSerializer(serializers.ModelSerializer):
    nom = serializers.CharField(source="name", read_only=True)
    code = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "nom", "code", "description"]

    def get_code(self, instance):
        return permission_code(instance)

    def get_description(self, instance):
        return ""


class PermissionWriteSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=100)
    code = serializers.CharField(max_length=100)

    def validate_code(self, value):
        try:
            permission_identity(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error)) from error
        return value


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Role
        fields = ["id", "nom", "description", "permissions"]


class RoleWriteSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    permissions = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )


class RolePermissionSerializer(serializers.Serializer):
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
    )


class EmployeeRoleSerializer(serializers.Serializer):
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
    )
