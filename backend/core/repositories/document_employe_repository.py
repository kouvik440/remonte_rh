from django.db.models import QuerySet

from core.interfaces.document_employe_repository import DocumentEmployeRepositoryInterface
from core.models import DocumentEmploye


class DocumentEmployeRepository(DocumentEmployeRepositoryInterface):
    def all(self) -> QuerySet:
        return DocumentEmploye.objects.select_related("document", "employe").all()

    def for_employee(self, employee_id: int) -> QuerySet:
        return self.all().filter(employe_id=employee_id)

    def get(self, document_employe_id: int) -> DocumentEmploye:
        return DocumentEmploye.objects.get(pk=document_employe_id)

    def create(self, data: dict) -> DocumentEmploye:
        return DocumentEmploye.objects.create(**data)

    def update(self, document_employe: DocumentEmploye, data: dict) -> DocumentEmploye:
        for field, value in data.items():
            setattr(document_employe, field, value)
        document_employe.save()
        return document_employe

    def delete(self, document_employe: DocumentEmploye) -> None:
        document_employe.delete()
