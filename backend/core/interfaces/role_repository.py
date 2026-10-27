from abc import ABC, abstractmethod

from django.contrib.auth.models import Permission
from django.db.models import QuerySet

from core.models import Role


class RoleRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, role_id: int) -> Role:
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> Role:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Role:
        raise NotImplementedError

    @abstractmethod
    def update(self, role: Role, data: dict) -> Role:
        raise NotImplementedError

    @abstractmethod
    def delete(self, role: Role) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_permissions(self, role: Role, permissions: list) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_permissions(self, role: Role, permissions: list) -> None:
        raise NotImplementedError


class PermissionRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, permission_id: int) -> Permission:
        raise NotImplementedError

    @abstractmethod
    def get_by_name(self, name: str) -> Permission:
        raise NotImplementedError

    @abstractmethod
    def get_by_code(self, code: str) -> Permission:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Permission:
        raise NotImplementedError

    @abstractmethod
    def update(self, permission: Permission, data: dict) -> Permission:
        raise NotImplementedError

    @abstractmethod
    def delete(self, permission: Permission) -> None:
        raise NotImplementedError
