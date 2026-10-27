from abc import ABC, abstractmethod
from datetime import date

from django.db.models import QuerySet

from core.models import Contrat


class ContratRepositoryInterface(ABC):
    @abstractmethod
    def all(self, employee_id: int = None) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def for_employee_period(
        self,
        employee_id: int,
        date_debut: date,
        date_fin: date,
    ) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, contrat_id: int) -> Contrat:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Contrat:
        raise NotImplementedError

    @abstractmethod
    def update(self, contrat: Contrat, data: dict) -> Contrat:
        raise NotImplementedError

    @abstractmethod
    def delete(self, contrat: Contrat) -> None:
        raise NotImplementedError
