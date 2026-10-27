from django.db.models import QuerySet

from core.interfaces.document_employe_repository import DocumentEmployeRepositoryInterface
from core.models import DocumentEmploye
from core.repositories.document_employe_repository import DocumentEmployeRepository


class DocumentEmployeService:
    def __init__(self, repository: DocumentEmployeRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get_for_employee(self, employee_id: int) -> QuerySet:
        return self.repository.for_employee(employee_id)

    def get(self, document_employe_id: int) -> DocumentEmploye:
        return self.repository.get(document_employe_id)

    def create(self, data: dict) -> DocumentEmploye:
        return self.repository.create(data)

    def update(self, document_employe_id: int, data: dict) -> DocumentEmploye:
        document_employe = self.repository.get(document_employe_id)
        return self.repository.update(document_employe, data)

    def delete(self, document_employe_id: int) -> None:
        document_employe = self.repository.get(document_employe_id)
        self.repository.delete(document_employe)


document_employe_service = DocumentEmployeService(DocumentEmployeRepository())
