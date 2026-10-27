from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import DocumentEmploye


class DocumentEmployeRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def for_employee(self, employee_id: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, document_employe_id: int) -> DocumentEmploye:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> DocumentEmploye:
        raise NotImplementedError

    @abstractmethod
    def update(
        self, document_employe: DocumentEmploye, data: dict
    ) -> DocumentEmploye:
        raise NotImplementedError

    @abstractmethod
    def delete(self, document_employe: DocumentEmploye) -> None:
        raise NotImplementedError