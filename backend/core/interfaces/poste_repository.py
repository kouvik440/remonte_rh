from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import Poste


class PosteRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get(self, poste_id: int) -> Poste:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> Poste:
        raise NotImplementedError

    @abstractmethod
    def update(self, poste: Poste, data: dict) -> Poste:
        raise NotImplementedError

    @abstractmethod
    def delete(self, poste: Poste) -> None:
        raise NotImplementedError