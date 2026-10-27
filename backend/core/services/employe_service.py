from datetime import date

from django.db.models import QuerySet
from django.db import transaction
from rest_framework.exceptions import ValidationError

from core.interfaces.employe_repository import EmployeRepositoryInterface
from core.interfaces.role_repository import RoleRepositoryInterface
from core.models import Employe
from .employe_history_service import record_change, manager_snapshot
from core.repositories.employe_repository import EmployeRepository
from core.repositories.role_repository import RoleRepository


class EmployeService:
    def __init__(
        self,
        repository: EmployeRepositoryInterface,
        role_repository: RoleRepositoryInterface,
    ):
        self.repository = repository
        self.role_repository = role_repository

    def get_all(self, **filters) -> QuerySet:
        return self.repository.all(**filters)

    def get_for_calendar(
        self,
        date_debut: date,
        date_fin: date,
        department_id: int = None,
        employee_id: int = None,
    ) -> QuerySet:
        return self.repository.for_calendar(
            date_debut,
            date_fin,
            department_id=department_id,
            employee_id=employee_id,
        )

    def get(self, employee_id: int) -> Employe:
        return self.repository.get(employee_id)

    @transaction.atomic
    def create(self, data: dict, actor=None) -> Employe:
        data = dict(data)
        self._validate_manager(None, data.get("responsable"))
        employee = self.repository.create(self._resolve_roles(data))
        if employee.responsable_id:
            record_change(employee.pk, "RESPONSABLE", employee.pk, {}, manager_snapshot(employee), actor)
        return self.repository.get(employee.pk)

    @transaction.atomic
    def update(self, employee_id: int, data: dict, actor=None) -> Employe:
        data = dict(data)
        if "responsable" in data:
            self._validate_manager(employee_id, data["responsable"])
        employee = self.repository.get(employee_id)
        before = manager_snapshot(employee)
        updated = self.repository.update(employee, self._resolve_roles(data))
        record_change(employee_id, "RESPONSABLE", employee_id, before, manager_snapshot(updated), actor)
        return self.repository.get(employee_id)

    @staticmethod
    def _validate_manager(employee_id, manager):
        if manager is None:
            return
        # Serialize hierarchy edits so two concurrent updates cannot create a cycle.
        hierarchy = dict(Employe.objects.select_for_update().order_by("pk").values_list("pk", "responsable_id"))
        visited = {employee_id} if employee_id else set()
        current = manager.pk
        while current is not None:
            if current in visited:
                raise ValidationError({"responsable": "Ce rattachement créerait une boucle hiérarchique."})
            visited.add(current)
            current = hierarchy.get(current)
        if not manager.is_active and (not employee_id or hierarchy.get(employee_id) != manager.pk):
            raise ValidationError({"responsable": "Choisissez un responsable dont le compte est actif."})

    def add_roles(self, employee_id: int, role_ids: list) -> Employe:
        employee = self.repository.get(employee_id)
        roles = [self.role_repository.get(role_id) for role_id in role_ids]
        self.repository.add_roles(employee, roles)
        return self.repository.get(employee_id)

    def remove_roles(self, employee_id: int, role_ids: list) -> Employe:
        employee = self.repository.get(employee_id)
        roles = [self.role_repository.get(role_id) for role_id in role_ids]
        self.repository.remove_roles(employee, roles)
        return self.repository.get(employee_id)

    def delete(self, employee_id: int) -> None:
        employee = self.repository.get(employee_id)
        self.repository.delete(employee)

    def _resolve_roles(self, data: dict) -> dict:
        resolved_data = dict(data)
        if "roles" in resolved_data:
            resolved_data["roles"] = [
                self.role_repository.get(role_id)
                for role_id in resolved_data["roles"]
            ]
        return resolved_data


employe_service = EmployeService(EmployeRepository(), RoleRepository())
