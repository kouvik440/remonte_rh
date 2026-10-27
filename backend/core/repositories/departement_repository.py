from django.db.models import QuerySet

from core.interfaces.departement_repository import DepartementRepositoryInterface
from core.models import Departement


class DepartementRepository(DepartementRepositoryInterface):
    def all(self) -> QuerySet:
        return Departement.objects.all()

    def get(self, department_id: int) -> Departement:
        return Departement.objects.get(pk=department_id)

    def create(self, data: dict) -> Departement:
        return Departement.objects.create(**data)

    def update(self, department: Departement, data: dict) -> Departement:
        for field, value in data.items():
            setattr(department, field, value)
        department.save()
        return department

    def delete(self, department: Departement) -> None:
        department.delete()
