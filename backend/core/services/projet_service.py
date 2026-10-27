from django.db.models import QuerySet
from django.db.models.deletion import ProtectedError
from uuid import uuid4
from rest_framework.exceptions import ValidationError

from core.interfaces.projet_repository import ProjetRepositoryInterface
from core.models import AffectationProjet, Projet, TacheProjet
from core.repositories.projet_repository import ProjetRepository


class ProjetService:
    def __init__(self, repository: ProjetRepositoryInterface):
        self.repository = repository

    def get_all_projects(self) -> QuerySet:
        return self.repository.all_projects()

    def get_project(self, project_id: int) -> Projet:
        return self.repository.get_project(project_id)

    def create_project(self, data: dict) -> Projet:
        self._validate_dates(data)
        return self.repository.create_project({**data, "code": f"PROJ_{uuid4().hex[:24].upper()}"})

    def update_project(self, project_id: int, data: dict) -> Projet:
        project = self.repository.get_project(project_id)
        self._validate_dates(
            {
                "date_debut": data.get("date_debut", project.date_debut),
                "date_fin": data.get("date_fin", project.date_fin),
            }
        )
        return self.repository.update_project(project, {key: value for key, value in data.items() if key != "code"})

    def delete_project(self, project_id: int) -> None:
        self.repository.delete_project(self.repository.get_project(project_id))

    def get_tasks(self, project_id: int) -> QuerySet:
        self.repository.get_project(project_id)
        return self.repository.tasks_for_project(project_id)

    def get_task(self, task_id: int) -> TacheProjet:
        return self.repository.get_task(task_id)

    def create_task(self, project_id: int, data: dict) -> TacheProjet:
        project = self.repository.get_project(project_id)
        return self.repository.create_task({**data, "projet": project, "code": f"TASK_{uuid4().hex[:24].upper()}"})

    def update_task(self, task_id: int, data: dict) -> TacheProjet:
        task = self.repository.get_task(task_id)
        return self.repository.update_task(task, {key: value for key, value in data.items() if key != "code"})

    def delete_task(self, task_id: int) -> None:
        try:
            self.repository.delete_task(self.repository.get_task(task_id))
        except ProtectedError as error:
            raise ValidationError({"detail": "Cette tâche est utilisée dans une feuille de temps et ne peut pas être supprimée."}) from error

    def get_assignments(
        self,
        project_id: int,
        employee_id: int = None,
    ) -> QuerySet:
        self.repository.get_project(project_id)
        return self.repository.assignments_for_project(
            project_id,
            employee_id=employee_id,
        )

    def assign_employee(self, project_id: int, employee_id: int) -> AffectationProjet:
        project = self.repository.get_project(project_id)
        assignment, created = self.repository.assign_employee(project, employee_id)
        if not created:
            raise ValidationError(
                {"employe": "Cet employé est déjà affecté à ce projet."}
            )
        return assignment

    def remove_assignment(self, project_id: int, employee_id: int) -> None:
        self.repository.get_project(project_id)
        if not self.repository.remove_assignment(project_id, employee_id):
            raise AffectationProjet.DoesNotExist

    @staticmethod
    def _validate_dates(data: dict) -> None:
        date_debut = data.get("date_debut")
        date_fin = data.get("date_fin")
        if date_debut and date_fin and date_fin < date_debut:
            raise ValidationError(
                {"date_fin": "La date de fin doit être égale ou postérieure au début."}
            )


projet_service = ProjetService(ProjetRepository())
