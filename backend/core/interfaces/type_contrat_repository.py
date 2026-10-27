from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import TypeContrat


class ContractTypeInUseError(Exception):
    pass


class TypeContratRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, type_contrat_id: int) -> TypeContrat:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> TypeContrat:
        raise NotImplementedError

    @abstractmethod
    def update(self, type_contrat: TypeContrat, data: dict) -> TypeContrat:
        raise NotImplementedError

    @abstractmethod
    def delete(self, type_contrat: TypeContrat) -> None:
        raise NotImplementedError
