from abc import ABC, abstractmethod
from datetime import date

from django.db.models import QuerySet

from core.models import FeuilleTemps, Projet


class FeuilleTempsRepositoryInterface(ABC):
    @abstractmethod
    def for_employee(
        self,
        employee_id: int,
        week_start: date = None,
        work_date: date = None,
    ) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_for_employee(self, sheet_id: int, employee_id: int) -> FeuilleTemps:
        raise NotImplementedError

    @abstractmethod
    def get_for_employee_for_update(self, sheet_id: int, employee_id: int) -> FeuilleTemps:
        raise NotImplementedError

    @abstractmethod
    def submitted_for_decision(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def active_projects_for_employee(self, employee_id: int, pending_only=False) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_for_decision(self, sheet_id: int) -> FeuilleTemps:
        raise NotImplementedError

    @abstractmethod
    def create(self, employee_id: int, week_start: date) -> tuple[FeuilleTemps, bool]:
        raise NotImplementedError

    @abstractmethod
    def replace_lines(self, sheet: FeuilleTemps, lines: list) -> FeuilleTemps:
        raise NotImplementedError

    @abstractmethod
    def set_status(self, sheet: FeuilleTemps, status: str) -> FeuilleTemps:
        raise NotImplementedError

    @abstractmethod
    def record_decision(
        self,
        sheet: FeuilleTemps,
        status: str,
        reviewer_id: int,
        decided_at,
        rejection_reason: str = "",
    ) -> FeuilleTemps:
        raise NotImplementedError

    @abstractmethod
    def delete(self, sheet: FeuilleTemps) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_project_assignment(self, employee_id: int, project_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_active_project_and_task(self, project_id: int, task_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def contracts_for_date(self, employee_id: int, work_date: date) -> QuerySet:
        raise NotImplementedError
