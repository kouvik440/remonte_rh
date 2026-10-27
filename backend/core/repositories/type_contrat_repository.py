from django.db.models import QuerySet
from django.db.models.deletion import ProtectedError

from core.interfaces.type_contrat_repository import ContractTypeInUseError, TypeContratRepositoryInterface
from core.models import TypeContrat


class TypeContratRepository(TypeContratRepositoryInterface):
    def all(self) -> QuerySet:
        return TypeContrat.objects.all()

    def get(self, type_contrat_id: int) -> TypeContrat:
        return TypeContrat.objects.get(pk=type_contrat_id)

    def create(self, data: dict) -> TypeContrat:
        return TypeContrat.objects.create(**data)

    def update(self, type_contrat: TypeContrat, data: dict) -> TypeContrat:
        for field, value in data.items():
            setattr(type_contrat, field, value)
        type_contrat.save()
        return type_contrat

    def delete(self, type_contrat: TypeContrat) -> None:
        try:
            type_contrat.delete()
        except ProtectedError as error:
            raise ContractTypeInUseError from error
