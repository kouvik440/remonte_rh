from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import DemandeAbsence, SoldeConge


class SoldeCongeRepositoryInterface(ABC):
    @abstractmethod
    def entitlements(self, year: int, employee_id: int = None) -> list:
        raise NotImplementedError

    @abstractmethod
    def lock_employee(self, employee_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def all(self, year: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def for_employee(self, employee_id: int, year: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_for_employee_type_year(self, employee_id: int, type_conge_id: int, year: int):
        raise NotImplementedError

    @abstractmethod
    def reserved_absences(self, employee_id: int, type_conge_id: int, year: int, exclude_id: int = None) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> SoldeConge:
        raise NotImplementedError

    @abstractmethod
    def update_used_days(self, balance: SoldeConge, used_days: int) -> SoldeConge:
        raise NotImplementedError

    @abstractmethod
    def approved_absences(
        self, year: int, employee_id: int = None, *, leave_type_id: int = None
    ) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def pending_absences(self, year: int, employee_id: int = None) -> QuerySet:
        raise NotImplementedError
