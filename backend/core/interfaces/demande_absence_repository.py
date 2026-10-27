from abc import ABC, abstractmethod
from typing import Optional

from django.db.models import QuerySet

from core.models import DemandeAbsence


class DemandeAbsenceRepositoryInterface(ABC):
    @abstractmethod
    def all(self) -> QuerySet:
        raise NotImplementedError
    
    @abstractmethod
    def for_employee(self, employee_id: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def calendar(
        self,
        date_debut,
        date_fin,
        department_id: int = None,
        employee_id: int = None,
    ) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def find_approved_overlap(
        self,
        employee_id: int,
        date_debut,
        date_fin,
        exclude_demande_id: int = None,
    ) -> Optional[DemandeAbsence]:
        raise NotImplementedError

    @abstractmethod
    def get(self, demande_absence_id: int) -> DemandeAbsence:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: dict) -> DemandeAbsence:
        raise NotImplementedError

    @abstractmethod
    def update(
        self, demande_absence: DemandeAbsence, data: dict
    ) -> DemandeAbsence:
        raise NotImplementedError

    @abstractmethod
    def delete(self, demande_absence: DemandeAbsence) -> None:
        raise NotImplementedError
