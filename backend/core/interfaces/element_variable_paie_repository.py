from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import ElementVariablePaie


class ElementVariablePaieRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def filtered(self, employee_id: int = None, periode: str = None) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, element_id: int) -> ElementVariablePaie:
        raise NotImplementedError

    @abstractmethod
    def for_employee_period(self, employee_id: int, periode: str) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> ElementVariablePaie:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        element: ElementVariablePaie,
        data: dict,
    ) -> ElementVariablePaie:
        raise NotImplementedError

    @abstractmethod
    def delete(self, element: ElementVariablePaie) -> None:
        raise NotImplementedError