from django.db.models import QuerySet
from django.db import transaction

from core.interfaces.document_repository import DocumentRepositoryInterface
from core.models import Document


class DocumentRepository(DocumentRepositoryInterface):
    def for_employee(self, employee_id: int) -> QuerySet:
        return self.all().filter(employes__pk=employee_id).distinct()

    def belongs_to(self, document_id: int, employee_id: int) -> bool:
        return Document.objects.filter(pk=document_id, employes__pk=employee_id).exists()

    def all(self) -> QuerySet:
        return Document.objects.select_related("type_document").prefetch_related("employes").all()

    def get(self, document_id: int) -> Document:
        return self.all().get(pk=document_id)

    @transaction.atomic
    def create(self, data: dict) -> Document:
        employes = data.pop("employes", [])
        document = Document.objects.create(**data)
        if employes:
            document.employes.set(employes)
        return document

    @transaction.atomic
    def update(self, document: Document, data: dict) -> Document:
        employes = data.pop("employes", None)
        for field, value in data.items():
            setattr(document, field, value)
        document.save()
        if employes is not None:
            document.employes.set(employes)
        return document

    def delete(self, document: Document) -> None:
        document.delete()
