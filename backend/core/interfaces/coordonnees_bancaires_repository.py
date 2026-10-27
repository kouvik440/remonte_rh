from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import CoordonneesBancaires


class BankIbanAlreadyUsedError(Exception):
    pass


class CoordonneesBancairesRepositoryInterface(ABC):
    @abstractmethod
    def iban_exists(self, fingerprint: str, exclude_id: int = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def for_employee(self, employee_id: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, coordonnees_bancaires_id: int) -> CoordonneesBancaires:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> CoordonneesBancaires:
        raise NotImplementedError

    @abstractmethod
    def update(
        self, coordonnees_bancaires: CoordonneesBancaires, data: dict
    ) -> CoordonneesBancaires:
        raise NotImplementedError

    @abstractmethod
    def delete(self, coordonnees_bancaires: CoordonneesBancaires) -> None:
        raise NotImplementedError
