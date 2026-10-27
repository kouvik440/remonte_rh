from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import TypeConge


class LeaveTypeInUseError(Exception):
    pass


class TypeCongeRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, type_conge_id: int) -> TypeConge:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> TypeConge:
        raise NotImplementedError

    @abstractmethod
    def update(self, type_conge: TypeConge, data: dict) -> TypeConge:
        raise NotImplementedError

    @abstractmethod
    def delete(self, type_conge: TypeConge) -> None:
        raise NotImplementedError


