from abc import ABC, abstractmethod
from datetime import date

from django.db.models import QuerySet

from core.models import ReglePaie


class ReglePaieRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, regle_id: int) -> ReglePaie:
        raise NotImplementedError

    @abstractmethod
    def for_period(self, date_debut: date, date_fin: date) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> ReglePaie:
        raise NotImplementedError

    @abstractmethod
    def update(self, regle: ReglePaie, data: dict) -> ReglePaie:
        raise NotImplementedError

    @abstractmethod
    def delete(self, regle: ReglePaie) -> None:
        raise NotImplementedError