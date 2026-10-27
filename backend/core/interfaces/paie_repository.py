from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import Paie


class PaieRepositoryInterface(ABC):
    @abstractmethod
    def get_for_update(self, paie_id: int) -> Paie:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def for_employee(self, employee_id: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def exists_for_employee_period(
        self,
        employee_id: int,
        periode: str,
        exclude_paie_id: int = None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, paie_id: int) -> Paie:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Paie:
        raise NotImplementedError

    @abstractmethod
    def update(self, paie: Paie, data: dict) -> Paie:
        raise NotImplementedError

    @abstractmethod
    def save_bulletin(self, paie: Paie, filename: str, content: bytes) -> Paie:
        raise NotImplementedError

    @abstractmethod
    def get_classification_snapshot(self, employee_id: int, contract_id: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def order_used_by_other_payroll(self, ordre_virement_id: int, paie_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self, paie: Paie) -> None:
        raise NotImplementedError
