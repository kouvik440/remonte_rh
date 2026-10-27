from abc import ABC, abstractmethod

from django.db.models import QuerySet

from core.models import AffectationProjet, Projet, TacheProjet


class ProjetRepositoryInterface(ABC):
    @abstractmethod
    def all_projects(self) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_project(self, project_id: int) -> Projet:
        raise NotImplementedError

    @abstractmethod
    def create_project(self, data: dict) -> Projet:
        raise NotImplementedError

    @abstractmethod
    def update_project(self, project: Projet, data: dict) -> Projet:
        raise NotImplementedError

    @abstractmethod
    def delete_project(self, project: Projet) -> None:
        raise NotImplementedError

    @abstractmethod
    def tasks_for_project(self, project_id: int) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def get_task(self, task_id: int) -> TacheProjet:
        raise NotImplementedError

    @abstractmethod
    def create_task(self, data: dict) -> TacheProjet:
        raise NotImplementedError

    @abstractmethod
    def update_task(self, task: TacheProjet, data: dict) -> TacheProjet:
        raise NotImplementedError

    @abstractmethod
    def delete_task(self, task: TacheProjet) -> None:
        raise NotImplementedError

    @abstractmethod
    def assignments_for_project(
        self,
        project_id: int,
        employee_id: int = None,
    ) -> QuerySet:
        raise NotImplementedError

    @abstractmethod
    def assign_employee(
        self,
        project: Projet,
        employee_id: int,
    ) -> tuple[AffectationProjet, bool]:
        raise NotImplementedError

    @abstractmethod
    def remove_assignment(self, project_id: int, employee_id: int) -> int:
        raise NotImplementedError
