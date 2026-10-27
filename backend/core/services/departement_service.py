from uuid import uuid4

from django.db.models import QuerySet

from core.interfaces.departement_repository import DepartementRepositoryInterface
from core.models import Departement
from core.repositories.departement_repository import DepartementRepository


class DepartementService:
    def __init__(self, repository: DepartementRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, department_id: int) -> Departement:
        return self.repository.get(department_id)

    def create(self, data: dict) -> Departement:
        department_data = {**data, "code": f"DEP_{uuid4().hex[:16].upper()}"}
        return self.repository.create(department_data)

    def update(self, department_id: int, data: dict) -> Departement:
        department = self.repository.get(department_id)
        department_data = {key: value for key, value in data.items() if key != "code"}
        return self.repository.update(department, department_data)

    def delete(self, department_id: int) -> None:
        department = self.repository.get(department_id)
        self.repository.delete(department)


departement_service = DepartementService(DepartementRepository())
