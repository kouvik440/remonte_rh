from django.db.models import QuerySet

from core.interfaces.document_repository import DocumentRepositoryInterface
from core.models import Document
from core.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, repository: DocumentRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get_for_employee(self, employee_id: int) -> QuerySet:
        return self.repository.for_employee(employee_id)

    def belongs_to(self, document_id: int, employee_id: int) -> bool:
        return self.repository.belongs_to(document_id, employee_id)

    def get(self, document_id: int) -> Document:
        return self.repository.get(document_id)

    def create(self, data: dict) -> Document:
        return self.repository.create(data)

    def update(self, document_id: int, data: dict) -> Document:
        document = self.repository.get(document_id)
        return self.repository.update(document, data)

    def delete(self, document_id: int) -> None:
        document = self.repository.get(document_id)
        self.repository.delete(document)


document_service = DocumentService(DocumentRepository())
