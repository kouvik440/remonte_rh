from django.db.models import QuerySet

from core.interfaces.projet_repository import ProjetRepositoryInterface
from core.models import AffectationProjet, Employe, Projet, TacheProjet


class ProjetRepository(ProjetRepositoryInterface):
    def all_projects(self) -> QuerySet:
        return Projet.objects.all()

    def get_project(self, project_id: int) -> Projet:
        return Projet.objects.get(pk=project_id)

    def create_project(self, data: dict) -> Projet:
        return Projet.objects.create(**data)

    def update_project(self, project: Projet, data: dict) -> Projet:
        for field, value in data.items():
            setattr(project, field, value)
        project.save()
        return project

    def delete_project(self, project: Projet) -> None:
        project.delete()

    def tasks_for_project(self, project_id: int) -> QuerySet:
        return TacheProjet.objects.filter(projet_id=project_id)

    def get_task(self, task_id: int) -> TacheProjet:
        return TacheProjet.objects.get(pk=task_id)

    def create_task(self, data: dict) -> TacheProjet:
        return TacheProjet.objects.create(**data)

    def update_task(self, task: TacheProjet, data: dict) -> TacheProjet:
        for field, value in data.items():
            setattr(task, field, value)
        task.save()
        return task

    def delete_task(self, task: TacheProjet) -> None:
        task.delete()

    def assignments_for_project(
        self,
        project_id: int,
        employee_id: int = None,
    ) -> QuerySet:
        assignments = AffectationProjet.objects.filter(
            projet_id=project_id
        ).select_related("employe")
        if employee_id is not None:
            assignments = assignments.filter(employe_id=employee_id)
        return assignments

    def assign_employee(
        self,
        project: Projet,
        employee_id: int,
    ) -> tuple[AffectationProjet, bool]:
        employee = Employe.objects.get(pk=employee_id)
        return AffectationProjet.objects.get_or_create(
            projet=project,
            employe=employee,
        )

    def remove_assignment(self, project_id: int, employee_id: int) -> int:
        deleted, _ = AffectationProjet.objects.filter(
            projet_id=project_id,
            employe_id=employee_id,
        ).delete()
        return deleted
