from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import Departement


class DepartementRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, department_id: int) -> Departement:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Departement:
        raise NotImplementedError

    @abstractmethod
    def update(self, department: Departement, data: dict) -> Departement:
        raise NotImplementedError

    @abstractmethod
    def delete(self, department: Departement) -> None:
        raise NotImplementedError