from django.db.models import QuerySet
from typing import Optional

from core.interfaces.demande_absence_repository import DemandeAbsenceRepositoryInterface
from core.models import DemandeAbsence
from core.models.enums import StatutAbsence


class DemandeAbsenceRepository(DemandeAbsenceRepositoryInterface):
    def all(self) -> QuerySet:
        return DemandeAbsence.objects.select_related(
            "employe",
            "employe__department",
            "type_conge",
        ).all()
    
    def for_employee(self, employee_id: int) -> QuerySet:
        return self.all().filter(employe_id=employee_id)

    def calendar(
        self,
        date_debut,
        date_fin,
        department_id: int = None,
        employee_id: int = None,
    ) -> QuerySet:
        demandes = self.all().filter(
            statut=StatutAbsence.VALIDEE,
            date_debut__lte=date_fin,
            date_fin__gte=date_debut,
        )
        if department_id is not None:
            demandes = demandes.filter(employe__department_id=department_id)
        if employee_id is not None:
            demandes = demandes.filter(employe_id=employee_id)
        return demandes.order_by("date_debut", "employe__nom", "employe__prenom")

    def find_approved_overlap(
        self,
        employee_id: int,
        date_debut,
        date_fin,
        exclude_demande_id: int = None,
    ) -> Optional[DemandeAbsence]:
        demandes = self.all().filter(
            employe_id=employee_id,
            statut=StatutAbsence.VALIDEE,
            date_debut__lte=date_fin,
            date_fin__gte=date_debut,
        )
        if exclude_demande_id is not None:
            demandes = demandes.exclude(pk=exclude_demande_id)
        return demandes.order_by("date_debut", "pk").first()

    def get(self, demande_absence_id: int) -> DemandeAbsence:
        return self.all().select_related("valideur").get(pk=demande_absence_id)

    def create(self, data: dict) -> DemandeAbsence:
        return DemandeAbsence.objects.create(**data)

    def update(self, demande_absence: DemandeAbsence, data: dict) -> DemandeAbsence:
        for field, value in data.items():
            setattr(demande_absence, field, value)
        demande_absence.save()
        return demande_absence

    def delete(self, demande_absence: DemandeAbsence) -> None:
        demande_absence.delete()
