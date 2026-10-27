from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from core.interfaces.type_contrat_repository import ContractTypeInUseError, TypeContratRepositoryInterface
from core.models import TypeContrat
from core.repositories.type_contrat_repository import TypeContratRepository


class TypeContratService:
    def __init__(self, repository: TypeContratRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, type_contrat_id: int) -> TypeContrat:
        return self.repository.get(type_contrat_id)

    def create(self, data: dict) -> TypeContrat:
        return self.repository.create(data)

    def update(self, type_contrat_id: int, data: dict) -> TypeContrat:
        type_contrat = self.repository.get(type_contrat_id)
        return self.repository.update(type_contrat, data)

    def delete(self, type_contrat_id: int) -> None:
        type_contrat = self.repository.get(type_contrat_id)
        try:
            self.repository.delete(type_contrat)
        except ContractTypeInUseError as error:
            raise ValidationError({"type": "Ce type est utilisé par un contrat et ne peut pas être supprimé."}) from error


type_contrat_service = TypeContratService(TypeContratRepository())
