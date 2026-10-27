from django.db.models import QuerySet
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.interfaces.demande_absence_repository import DemandeAbsenceRepositoryInterface
from core.models import DemandeAbsence
from core.models.enums import StatutAbsence
from core.repositories.demande_absence_repository import DemandeAbsenceRepository
from core.services.solde_conge_service import solde_conge_service


class DemandeAbsenceService:
    def __init__(
        self,
        repository: DemandeAbsenceRepositoryInterface,
        solde_conge_service,
    ):
        self.repository = repository
        self.solde_conge_service = solde_conge_service

    def get_all(self) -> QuerySet:
        return self.repository.all()
    
    def get_for_employee(self, employee_id: int) -> QuerySet:
        return self.repository.for_employee(employee_id)

    def calendar(
        self,
        date_debut,
        date_fin,
        department_id: int = None,
        employee_id: int = None,
    ) -> QuerySet:
        return self.repository.calendar(
            date_debut,
            date_fin,
            department_id=department_id,
            employee_id=employee_id,
        )

    def get(self, demande_absence_id: int) -> DemandeAbsence:
        return self.repository.get(demande_absence_id)

    @transaction.atomic
    def create(self, data: dict) -> DemandeAbsence:
        self.solde_conge_service.validate_request_quota(
            data["employe"].pk,
            data["type_conge"],
            data["date_debut"],
            data["date_fin"],
        )
        return self.repository.create(data)

    @transaction.atomic
    def approve(self, demande_absence_id: int, valideur_id: int) -> DemandeAbsence:
        demande = self.repository.get(demande_absence_id)
        if demande.statut != StatutAbsence.EN_ATTENTE:
            raise ValidationError(
                {"statut": "Seule une demande en attente peut etre validee."}
            )
        conflit = self.repository.find_approved_overlap(
            demande.employe_id,
            demande.date_debut,
            demande.date_fin,
            exclude_demande_id=demande.pk,
        )
        if conflit and self._has_workday_overlap(demande, conflit):
            raise ValidationError(
                {
                    "date_debut": (
                        "Cette demande chevauche une autre absence déjà validée "
                        f"(demande {conflit.pk}, du {conflit.date_debut} au {conflit.date_fin})."
                    )
                }
            )
        self.solde_conge_service.validate_request_quota(
            demande.employe_id,
            demande.type_conge,
            demande.date_debut,
            demande.date_fin,
            exclude_request_id=demande.pk,
        )
        demande.statut = StatutAbsence.VALIDEE
        demande.valideur_id = valideur_id
        demande.date_validation = timezone.now()
        demande = self.repository.update(demande, {})
        self._refresh_balance(demande)
        return demande

    @staticmethod
    def _has_workday_overlap(first: DemandeAbsence, second: DemandeAbsence) -> bool:
        debut = max(first.date_debut, second.date_debut)
        fin = min(first.date_fin, second.date_fin)
        return any(
            (debut + timezone.timedelta(days=offset)).weekday() < 5
            for offset in range((fin - debut).days + 1)
        ) if debut <= fin else False

    def reject(self, demande_absence_id: int, valideur_id: int) -> DemandeAbsence:
        demande = self.repository.get(demande_absence_id)
        if demande.statut != StatutAbsence.EN_ATTENTE:
            raise ValidationError(
                {"statut": "Seule une demande en attente peut etre refusee."}
            )
        demande.statut = StatutAbsence.REFUSEE
        demande.valideur_id = valideur_id
        demande.date_validation = timezone.now()
        return self.repository.update(demande, {})

    def _refresh_balance(self, demande: DemandeAbsence) -> None:
        for year in range(demande.date_debut.year, demande.date_fin.year + 1):
            self.solde_conge_service.refresh_balance(
                demande.employe_id,
                demande.type_conge_id,
                year,
            )

    @transaction.atomic
    def update(self, demande_absence_id: int, data: dict) -> DemandeAbsence:
        demande_absence = self.repository.get(demande_absence_id)
        old_type_id = demande_absence.type_conge_id
        old_start = demande_absence.date_debut
        old_end = demande_absence.date_fin
        new_type = data.get("type_conge", demande_absence.type_conge)
        new_start = data.get("date_debut", old_start)
        new_end = data.get("date_fin", old_end)
        self.solde_conge_service.validate_request_quota(
            demande_absence.employe_id,
            new_type,
            new_start,
            new_end,
            exclude_request_id=demande_absence.pk,
        )
        updated = self.repository.update(demande_absence, data)
        if updated.statut == StatutAbsence.VALIDEE:
            self._refresh_balance_for_period(
                updated.employe_id,
                old_type_id,
                old_start,
                old_end,
            )
            self._refresh_balance_for_period(
                updated.employe_id,
                updated.type_conge_id,
                updated.date_debut,
                updated.date_fin,
            )
        return updated

    @transaction.atomic
    def delete(self, demande_absence_id: int) -> None:
        demande_absence = self.repository.get(demande_absence_id)
        employee_id = demande_absence.employe_id
        type_conge_id = demande_absence.type_conge_id
        date_debut = demande_absence.date_debut
        date_fin = demande_absence.date_fin
        was_approved = demande_absence.statut == StatutAbsence.VALIDEE
        self.repository.delete(demande_absence)
        if was_approved:
            self._refresh_balance_for_period(
                employee_id,
                type_conge_id,
                date_debut,
                date_fin,
            )

    def _refresh_balance_for_period(self, employee_id, type_conge_id, date_start, date_end):
        for year in range(date_start.year, date_end.year + 1):
            self.solde_conge_service.refresh_balance(employee_id, type_conge_id, year)


demande_absence_service = DemandeAbsenceService(
    DemandeAbsenceRepository(),
    solde_conge_service,
)
