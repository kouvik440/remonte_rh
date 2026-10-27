from datetime import date

from django.db import transaction
from django.db.models import Q, QuerySet, Prefetch
from django.utils import timezone

from core.models import Employe, Contrat
from core.models.enums import StatutEmploye
from core.interfaces.employe_repository import EmployeRepositoryInterface


class EmployeRepository(EmployeRepositoryInterface):
    @staticmethod
    def _with_directory_fields():
        today = timezone.localdate()
        contracts = Contrat.objects.filter(statut="EN_COURS", date_debut__lte=today).filter(Q(date_fin__isnull=True) | Q(date_fin__gte=today)).select_related("poste").prefetch_related("type")
        return Employe.objects.select_related("responsable").prefetch_related("roles", Prefetch("contrats", queryset=contracts, to_attr="contrats_actuels"))

    def all(self, poste=None, type_contrat=None) -> QuerySet:
        employees = self._with_directory_fields()
        if poste:
            today = timezone.localdate()
            contracts = Contrat.objects.filter(statut="EN_COURS", date_debut__lte=today, poste__nom__iexact=poste).filter(Q(date_fin__isnull=True) | Q(date_fin__gte=today))
            employees = employees.filter(pk__in=contracts.values("employe_id"))
        if type_contrat:
            today = timezone.localdate()
            contracts = Contrat.objects.filter(statut="EN_COURS", date_debut__lte=today, type__pk=type_contrat).filter(Q(date_fin__isnull=True) | Q(date_fin__gte=today))
            employees = employees.filter(pk__in=contracts.values("employe_id"))
        return employees

    def for_calendar(
        self,
        date_debut: date,
        date_fin: date,
        department_id: int = None,
        employee_id: int = None,
    ) -> QuerySet:
        employes = Employe.objects.select_related("department").filter(
            is_active=True,
            statut=StatutEmploye.ACTIF,
            date_entree__lte=date_fin,
        ).filter(Q(date_sortie__isnull=True) | Q(date_sortie__gte=date_debut))
        if department_id is not None:
            employes = employes.filter(department_id=department_id)
        if employee_id is not None:
            employes = employes.filter(pk=employee_id)
        return employes.order_by("nom", "prenom")

    def get(self, employee_id: int) -> Employe:
        return self._with_directory_fields().get(pk=employee_id)

    def create(self, data: dict) -> Employe:
        with transaction.atomic():
            password = data.pop("password", None)
            roles = data.pop("roles", [])
            employee = Employe.objects.create_user(
                email=data.pop("email"),
                password=password,
                is_active=data.pop("is_active", True),
                **data,
            )
            employee.roles.add(*roles)
            return self.get(employee.pk)

    def update(self, employee: Employe, data: dict) -> Employe:
        password = data.pop("password", None)
        roles = data.pop("roles", None)

        for field, value in data.items():
            setattr(employee, field, value)
        employee.save()

        if password:
            employee.set_password(password)
            employee.save(update_fields=["password"])

        if roles is not None:
            employee.roles.set(roles)
        return self.get(employee.pk)

    def delete(self, employee: Employe) -> None:
        employee.delete()

    def add_roles(self, employee: Employe, roles: list) -> None:
        employee.roles.add(*roles)

    def remove_roles(self, employee: Employe, roles: list) -> None:
        employee.roles.remove(*roles)
