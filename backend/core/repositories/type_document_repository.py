from django.db.models import QuerySet

from core.interfaces.type_document_repository import DocumentTypeInUseError, TypeDocumentRepositoryInterface
from core.models import TypeDocument


class TypeDocumentRepository(TypeDocumentRepositoryInterface):
    def all(self) -> QuerySet:
        return TypeDocument.objects.all()

    def get(self, type_document_id: int) -> TypeDocument:
        return TypeDocument.objects.get(pk=type_document_id)

    def create(self, data: dict) -> TypeDocument:
        return TypeDocument.objects.create(**data)

    def update(self, type_document: TypeDocument, data: dict) -> TypeDocument:
        for field, value in data.items():
            setattr(type_document, field, value)
        type_document.save()
        return type_document

    def delete(self, type_document: TypeDocument) -> None:
        if type_document.documents.exists():
            raise DocumentTypeInUseError
        type_document.delete()
