from abc import ABC, abstractmethod
from datetime import date

from django.db.models import QuerySet

from core.models import Employe, Role


class EmployeRepositoryInterface(ABC):
    @abstractmethod
    def all(self, poste=None, type_contrat=None) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def for_calendar(
        self,
        date_debut: date,
        date_fin: date,
        department_id: int = None,
        employee_id: int = None,
    ) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, employee_id: int) -> Employe:
        raise NotImplementedError
    
    @abstractmethod
    def create(self, data: dict) -> Employe:
        raise NotImplementedError

    @abstractmethod
    def update(self, employee: Employe, data: dict) -> Employe:
        raise NotImplementedError

    @abstractmethod
    def delete(self, employee: Employe) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_roles(self, employee: Employe, roles: list) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_roles(self, employee: Employe, roles: list) -> None:
        raise NotImplementedError
