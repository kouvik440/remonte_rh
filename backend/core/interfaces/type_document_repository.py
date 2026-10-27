from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import TypeDocument


class DocumentTypeInUseError(Exception):
    pass


class TypeDocumentRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, type_document_id: int) -> TypeDocument:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> TypeDocument:
        raise NotImplementedError

    @abstractmethod
    def update(self, type_document: TypeDocument, data: dict) -> TypeDocument:
        raise NotImplementedError

    @abstractmethod
    def delete(self, type_document: TypeDocument) -> None:
        raise NotImplementedError
