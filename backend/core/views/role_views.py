from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Permission

from core.services.role_service import role_service
from core.models import Role
from core.permissions import (
    HasPermissionCrudPermission,
    HasRoleAssignmentPermission,
    HasRoleCrudPermission,
)
from core.services.role_service import (
    DuplicatePermissionValueError,
    DuplicateRoleNameError,
)
from core.serializers.role_serializer import (
    PermissionSerializer,
    PermissionWriteSerializer,
    RolePermissionSerializer,
    RoleSerializer,
    RoleWriteSerializer,
)


class PermissionListView(APIView):
    permission_classes = [HasPermissionCrudPermission]
    service = role_service

    def get(self, request):
        permissions = self.service.get_all_permissions()
        return Response(PermissionSerializer(permissions, many=True).data)

    def post(self, request):
        serializer = PermissionWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            permission = self.service.create_permission(serializer.validated_data)
        except DuplicatePermissionValueError as error:
            return Response(
                {error.field: ["Cette valeur est déjà utilisée."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PermissionSerializer(permission).data, status=status.HTTP_201_CREATED)


class PermissionDetailView(APIView):
    permission_classes = [HasPermissionCrudPermission]
    service = role_service

    def get(self, request, permission_id):
        try:
            permission = self.service.get_permission(permission_id)
        except Permission.DoesNotExist:
            return Response({"detail": "Permission non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        return Response(PermissionSerializer(permission).data)

    def put(self, request, permission_id):
        serializer = PermissionWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            permission = self.service.update_permission(permission_id, serializer.validated_data)
        except Permission.DoesNotExist:
            return Response({"detail": "Permission non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        except DuplicatePermissionValueError as error:
            return Response(
                {error.field: ["Cette valeur est déjà utilisée."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(PermissionSerializer(permission).data)

    def delete(self, request, permission_id):
        try:
            self.service.delete_permission(permission_id)
        except Permission.DoesNotExist:
            return Response({"detail": "Permission non trouvée"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(APIView):
    permission_classes = [HasRoleCrudPermission]
    service = role_service

    def get(self, request):
        return Response(RoleSerializer(self.service.get_all(), many=True).data)

    def post(self, request):
        serializer = RoleWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            role = self.service.create(serializer.validated_data)
        except Permission.DoesNotExist:
            return Response(
                {"permissions": ["Une permission indiquée n'existe pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DuplicateRoleNameError:
            return Response(
                {"nom": ["Ce nom de rôle est déjà utilisé."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [HasRoleCrudPermission]
    service = role_service

    def get(self, request, role_id):
        try:
            return Response(RoleSerializer(self.service.get(role_id)).data)
        except Role.DoesNotExist:
            return Response({"detail": "Rôle non trouvé"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, role_id):
        serializer = RoleWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            role = self.service.update(role_id, serializer.validated_data)
        except Role.DoesNotExist:
            return Response({"detail": "Rôle non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        except Permission.DoesNotExist:
            return Response(
                {"permissions": ["Une permission indiquée n'existe pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DuplicateRoleNameError:
            return Response(
                {"nom": ["Ce nom de rôle est déjà utilisé."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(RoleSerializer(role).data)

    def delete(self, request, role_id):
        try:
            self.service.delete(role_id)
        except Role.DoesNotExist:
            return Response({"detail": "Rôle non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolePermissionView(APIView):
    permission_classes = [HasRoleAssignmentPermission]
    service = role_service

    def post(self, request, role_id):
        try:
            serializer = RolePermissionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            role = self.service.add_permissions(
                role_id,
                serializer.validated_data["permission_ids"],
            )
            return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response({"detail": "Rôle non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        except Permission.DoesNotExist:
            return Response(
                {"permission_ids": ["Une permission indiquée n'existe pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, role_id):
        try:
            serializer = RolePermissionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            role = self.service.remove_permissions(
                role_id,
                serializer.validated_data["permission_ids"],
            )
            return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response({"detail": "Rôle non trouvé"}, status=status.HTTP_404_NOT_FOUND)
        except Permission.DoesNotExist:
            return Response(
                {"permission_ids": ["Une permission indiquée n'existe pas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
