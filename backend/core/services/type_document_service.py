from django.db.models import QuerySet
from uuid import uuid4
from rest_framework.exceptions import ValidationError

from core.interfaces.type_document_repository import DocumentTypeInUseError, TypeDocumentRepositoryInterface
from core.models import TypeDocument
from core.repositories.type_document_repository import TypeDocumentRepository


class TypeDocumentService:
    def __init__(self, repository: TypeDocumentRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, type_document_id: int) -> TypeDocument:
        return self.repository.get(type_document_id)

    def create(self, data: dict) -> TypeDocument:
        return self.repository.create({**data, "code": f"DOC_{uuid4().hex[:14].upper()}"})

    def update(self, type_document_id: int, data: dict) -> TypeDocument:
        type_document = self.repository.get(type_document_id)
        return self.repository.update(type_document, {key: value for key, value in data.items() if key != "code"})

    def delete(self, type_document_id: int) -> None:
        type_document = self.repository.get(type_document_id)
        try:
            self.repository.delete(type_document)
        except DocumentTypeInUseError as error:
            raise ValidationError({"detail": "Ce type est utilisé. Désactivez-le pour conserver les documents."}) from error


type_document_service = TypeDocumentService(TypeDocumentRepository())
