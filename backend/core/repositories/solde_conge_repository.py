from datetime import date

from django.db.models import Q, QuerySet

from core.interfaces.solde_conge_repository import SoldeCongeRepositoryInterface
from core.models import DemandeAbsence, Employe, SoldeConge, TypeConge
from core.models.enums import StatutAbsence


class SoldeCongeRepository(SoldeCongeRepositoryInterface):
    def entitlements(self, year: int, employee_id: int = None) -> list:
        balances = self.all(year)
        employees = Employe.objects.filter(date_entree__lte=date(year, 12, 31)).filter(
            Q(date_sortie__isnull=True) | Q(date_sortie__gte=date(year, 1, 1))
        )
        if employee_id is not None:
            balances = balances.filter(employe_id=employee_id)
            employees = employees.filter(pk=employee_id)
        result = list(balances)
        existing = {(balance.employe_id, balance.type_conge_id) for balance in result}
        leave_types = list(TypeConge.objects.filter(actif=True))
        for employee in employees:
            for leave_type in leave_types:
                if (employee.pk, leave_type.pk) not in existing:
                    result.append(SoldeConge(
                        employe=employee, type_conge=leave_type, annee=year,
                        acquis=leave_type.jours_par_annee,
                    ))
        return result

    def lock_employee(self, employee_id: int) -> None:
        Employe.objects.select_for_update().only('pk').get(pk=employee_id)

    def all(self, year: int) -> QuerySet:
        return SoldeConge.objects.select_related("employe", "type_conge").filter(annee=year)

    def for_employee(self, employee_id: int, year: int) -> QuerySet:
        return self.all(year).filter(employe_id=employee_id)

    def get_for_employee_type_year(self, employee_id: int, type_conge_id: int, year: int):
        return self.all(year).filter(
            employe_id=employee_id,
            type_conge_id=type_conge_id,
        ).first()

    def reserved_absences(self, employee_id: int, type_conge_id: int, year: int, exclude_id: int = None) -> QuerySet:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        absences = DemandeAbsence.objects.filter(
            employe_id=employee_id,
            type_conge_id=type_conge_id,
            statut__in=[StatutAbsence.VALIDEE, StatutAbsence.EN_ATTENTE],
            date_debut__lte=end_date,
            date_fin__gte=start_date,
        )
        if exclude_id is not None:
            absences = absences.exclude(pk=exclude_id)
        return absences.only('date_debut', 'date_fin')

    def create(self, data: dict) -> SoldeConge:
        return SoldeConge.objects.create(**data)

    def update_used_days(self, balance: SoldeConge, used_days: int) -> SoldeConge:
        balance.pris = used_days
        balance.save(update_fields=["pris"])
        return balance

    def approved_absences(
        self, year: int, employee_id: int = None, *, leave_type_id: int = None
    ) -> QuerySet:
        absences = self._absences_for_status(year, StatutAbsence.VALIDEE, employee_id)
        if leave_type_id is not None:
            absences = absences.filter(type_conge_id=leave_type_id)
        return absences

    def pending_absences(self, year: int, employee_id: int = None) -> QuerySet:
        return self._absences_for_status(year, StatutAbsence.EN_ATTENTE, employee_id)

    @staticmethod
    def _absences_for_status(year: int, status: str, employee_id: int = None) -> QuerySet:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        absences = DemandeAbsence.objects.filter(
            statut=status,
            date_debut__lte=end_date,
            date_fin__gte=start_date,
        )
        if employee_id is not None:
            absences = absences.filter(employe_id=employee_id)
        return absences.only(
            "employe_id",
            "type_conge_id",
            "date_debut",
            "date_fin",
        )
