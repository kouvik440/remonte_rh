from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import OrdreVirement, Paie


class OrdreVirementRepositoryInterface(ABC):
    @abstractmethod
    def payroll_for_document(self, order: OrdreVirement, lock: bool = False) -> Paie:
        raise NotImplementedError

    @abstractmethod
    def save_document(self, order: OrdreVirement, snapshot: str, content: bytes, actor_id: int) -> OrdreVirement:
        raise NotImplementedError

    @abstractmethod
    def get_for_update(self, ordre_virement_id: int) -> OrdreVirement:
        raise NotImplementedError

    @abstractmethod
    def lock_employee(self, employee_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_active_order(self, employee_id: int, period: str, exclude_id: int = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_validated_payroll(self, employee_id: int, period: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, ordre_virement_id: int) -> OrdreVirement:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> OrdreVirement:
        raise NotImplementedError

    @abstractmethod
    def update(self, ordre_virement: OrdreVirement, data: dict) -> OrdreVirement:
        raise NotImplementedError

    @abstractmethod
    def delete(self, ordre_virement: OrdreVirement) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_paid_payroll(self, ordre_virement_id: int) -> bool:
        raise NotImplementedError
