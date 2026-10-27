from django.db.models import QuerySet
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from core.interfaces.role_repository import (
    PermissionRepositoryInterface,
    RoleRepositoryInterface,
)
from core.models import Role
from core.permission_codes import (
    CORE_PERMISSION_MODELS,
    permission_code,
    permission_identity,
)


class RoleRepository(RoleRepositoryInterface):
    def all(self) -> QuerySet:
        return Role.objects.prefetch_related("permissions").all()

    def get(self, role_id: int) -> Role:
        return Role.objects.prefetch_related("permissions").get(pk=role_id)

    def get_by_name(self, name: str) -> Role:
        return Role.objects.get(nom=name)

    def create(self, data: dict) -> Role:
        permissions = data.pop("permissions", [])
        role = Role.objects.create(**data)
        if permissions:
            role.permissions.set(permissions)
        return self.get(role.pk)

    def update(self, role: Role, data: dict) -> Role:
        permissions = data.pop("permissions", None)
        for field, value in data.items():
            setattr(role, field, value)
        role.save()
        if permissions is not None:
            role.permissions.set(permissions)
        return self.get(role.pk)

    def delete(self, role: Role) -> None:
        role.delete()

    def add_permissions(self, role: Role, permissions: list) -> None:
        role.permissions.add(*permissions)

    def remove_permissions(self, role: Role, permissions: list) -> None:
        role.permissions.remove(*permissions)


class PermissionRepository(PermissionRepositoryInterface):
    def all(self) -> QuerySet:
        return Permission.objects.filter(
            content_type__app_label="core",
            content_type__model__in=CORE_PERMISSION_MODELS,
        ).select_related("content_type")

    def get(self, permission_id: int) -> Permission:
        return self.all().get(pk=permission_id)

    def get_by_name(self, name: str) -> Permission:
        permission = self.all().filter(name__iexact=name).first()
        if permission is None:
            raise Permission.DoesNotExist
        return permission

    def get_by_code(self, code: str) -> Permission:
        model_name, codename = permission_identity(code)
        return self.all().get(
            content_type__model=model_name,
            codename=codename,
        )

    def create(self, data: dict) -> Permission:
        model_name, codename = permission_identity(data["code"])
        content_type = ContentType.objects.get(
            app_label="core",
            model=model_name,
        )
        return Permission.objects.create(
            name=data["nom"],
            codename=codename,
            content_type=content_type,
        )

    def update(self, permission: Permission, data: dict) -> Permission:
        model_name, codename = permission_identity(data.get("code", permission_code(permission)))
        permission.name = data.get("nom", permission.name)
        permission.codename = codename
        permission.content_type = ContentType.objects.get(
            app_label="core",
            model=model_name,
        )
        permission.save(update_fields=["name", "codename", "content_type"])
        return permission

    def delete(self, permission: Permission) -> None:
        permission.delete()
