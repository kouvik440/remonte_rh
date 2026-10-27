from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import Document


class DocumentRepositoryInterface(ABC):
    @abstractmethod
    def for_employee(self, employee_id: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def belongs_to(self, document_id: int, employee_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, document_id: int) -> Document:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Document:
        raise NotImplementedError

    @abstractmethod
    def update(self, document: Document, data: dict) -> Document:
        raise NotImplementedError

    @abstractmethod
    def delete(self, document: Document) -> None:
        raise NotImplementedError
