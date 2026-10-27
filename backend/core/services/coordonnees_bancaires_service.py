from django.db.models import QuerySet

from core.interfaces.coordonnees_bancaires_repository import BankIbanAlreadyUsedError, CoordonneesBancairesRepositoryInterface
from rest_framework.exceptions import ValidationError
from core.models import CoordonneesBancaires
from core.repositories.coordonnees_bancaires_repository import CoordonneesBancairesRepository


class CoordonneesBancairesService:
    def __init__(self, repository: CoordonneesBancairesRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get_for_employee(self, employee_id: int) -> QuerySet:
        return self.repository.for_employee(employee_id)

    def get(self, coordonnees_bancaires_id: int) -> CoordonneesBancaires:
        return self.repository.get(coordonnees_bancaires_id)

    def create(self, data: dict) -> CoordonneesBancaires:
        return self._persist(lambda: self.repository.create(data))

    def update(self, coordonnees_bancaires_id: int, data: dict) -> CoordonneesBancaires:
        coordonnees_bancaires = self.repository.get(coordonnees_bancaires_id)
        return self._persist(lambda: self.repository.update(coordonnees_bancaires, data))

    @staticmethod
    def _persist(operation) -> CoordonneesBancaires:
        try:
            return operation()
        except BankIbanAlreadyUsedError as error:
            raise ValidationError({"iban": "Cet IBAN est déjà utilisé."}) from error

    def delete(self, coordonnees_bancaires_id: int) -> None:
        coordonnees_bancaires = self.repository.get(coordonnees_bancaires_id)
        self.repository.delete(coordonnees_bancaires)


coordonnees_bancaires_service = CoordonneesBancairesService(
    CoordonneesBancairesRepository()
)
