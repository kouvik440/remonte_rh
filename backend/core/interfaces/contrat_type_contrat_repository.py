from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import ContratTypeContrat


class ContratTypeContratRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, contrat_type_contrat_id: int) -> ContratTypeContrat:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> ContratTypeContrat:
        raise NotImplementedError

    @abstractmethod
    def update(
        self, contrat_type_contrat: ContratTypeContrat, data: dict
    ) -> ContratTypeContrat:
        raise NotImplementedError

    @abstractmethod
    def delete(self, contrat_type_contrat: ContratTypeContrat) -> None:
        raise NotImplementedError