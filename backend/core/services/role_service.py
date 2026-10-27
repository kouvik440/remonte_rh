from django.db.models import QuerySet
from django.contrib.auth.models import Permission

from core.interfaces.role_repository import (
    PermissionRepositoryInterface,
    RoleRepositoryInterface,
)
from core.models import Role
from core.permission_codes import permission_code
from core.repositories.role_repository import PermissionRepository, RoleRepository


class DuplicateRoleNameError(Exception):
    pass


class DuplicatePermissionValueError(Exception):
    def __init__(self, field: str):
        self.field = field


class RoleService:
    def __init__(
        self,
        role_repository: RoleRepositoryInterface,
        permission_repository: PermissionRepositoryInterface,
    ):
        self.role_repository = role_repository
        self.permission_repository = permission_repository

    def get_all(self) -> QuerySet:
        return self.role_repository.all()

    def get(self, role_id: int) -> Role:
        return self.role_repository.get(role_id)

    def create(self, data: dict) -> Role:
        role_data = dict(data)
        self._ensure_role_name_available(role_data["nom"])
        if "permissions" in role_data:
            role_data["permissions"] = self._resolve_permissions(
                role_data["permissions"]
            )
        return self.role_repository.create(role_data)

    def update(self, role_id: int, data: dict) -> Role:
        role = self.role_repository.get(role_id)
        role_data = dict(data)
        if "nom" in role_data:
            self._ensure_role_name_available(role_data["nom"], exclude_id=role_id)
        if "permissions" in role_data:
            role_data["permissions"] = self._resolve_permissions(
                role_data["permissions"]
            )
        return self.role_repository.update(role, role_data)

    def delete(self, role_id: int) -> None:
        role = self.role_repository.get(role_id)
        self.role_repository.delete(role)

    def _ensure_role_name_available(self, name: str, exclude_id: int = None) -> None:
        try:
            existing_role = self.role_repository.get_by_name(name)
        except Role.DoesNotExist:
            return
        if existing_role.pk != exclude_id:
            raise DuplicateRoleNameError

    def _resolve_permissions(self, permission_ids: list) -> list:
        return [
            self.permission_repository.get(permission_id)
            for permission_id in permission_ids
        ]

    def add_permissions(self, role_id: int, permission_ids: list) -> Role:
        role = self.role_repository.get(role_id)
        permissions = [
            self.permission_repository.get(permission_id)
            for permission_id in permission_ids
        ]
        self.role_repository.add_permissions(role, permissions)
        return self.role_repository.get(role_id)

    def remove_permissions(self, role_id: int, permission_ids: list) -> Role:
        role = self.role_repository.get(role_id)
        permissions = [
            self.permission_repository.get(permission_id)
            for permission_id in permission_ids
        ]
        self.role_repository.remove_permissions(role, permissions)
        return self.role_repository.get(role_id)

    def get_all_permissions(self) -> QuerySet:
        return self.permission_repository.all()

    def get_permission(self, permission_id: int) -> Permission:
        return self.permission_repository.get(permission_id)

    def create_permission(self, data: dict) -> Permission:
        self._ensure_permission_values_available(data)
        return self.permission_repository.create(data)

    def update_permission(self, permission_id: int, data: dict) -> Permission:
        permission = self.permission_repository.get(permission_id)
        self._ensure_permission_values_available(data, exclude_id=permission_id)
        return self.permission_repository.update(permission, data)

    def delete_permission(self, permission_id: int) -> None:
        permission = self.permission_repository.get(permission_id)
        self.permission_repository.delete(permission)

    def _ensure_permission_values_available(
        self,
        data: dict,
        exclude_id: int = None,
    ) -> None:
        lookups = (
            ("nom", self.permission_repository.get_by_name),
            ("code", self.permission_repository.get_by_code),
        )
        for field, lookup in lookups:
            if field not in data:
                continue
            try:
                existing_permission = lookup(data[field])
            except Permission.DoesNotExist:
                continue
            if existing_permission.pk != exclude_id:
                raise DuplicatePermissionValueError(field)


role_service = RoleService(RoleRepository(), PermissionRepository())
