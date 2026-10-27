from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.interfaces.feuille_temps_repository import FeuilleTempsRepositoryInterface
from core.models import FeuilleTemps
from core.models.enums import StatutFeuilleTemps
from core.repositories.feuille_temps_repository import FeuilleTempsRepository


class FeuilleTempsService:
    def __init__(self, repository: FeuilleTempsRepositoryInterface):
        self.repository = repository

    def for_employee(
        self,
        employee_id: int,
        week_start: date = None,
        work_date: date = None,
    ) -> QuerySet:
        return self.repository.for_employee(
            employee_id,
            week_start=week_start,
            work_date=work_date,
        )

    def get_for_employee(self, sheet_id: int, employee_id: int) -> FeuilleTemps:
        return self.repository.get_for_employee(sheet_id, employee_id)

    def submitted_for_decision(self) -> QuerySet:
        return self.repository.submitted_for_decision()

    def active_projects_for_employee(self, employee_id: int, pending_only=False) -> QuerySet:
        return self.repository.active_projects_for_employee(employee_id, pending_only=pending_only)

    @transaction.atomic
    def create(self, employee_id: int, week_start: date, lines: list) -> FeuilleTemps:
        self._validate_week(week_start)
        lines = self._normalize_lines(employee_id, lines)
        self._validate_lines(employee_id, week_start, lines)
        sheet, created = self.repository.create(employee_id, week_start)
        if not created:
            raise ValidationError(
                {"semaine_debut": "Une feuille existe déjà pour cette semaine."}
            )
        return self.repository.replace_lines(sheet, lines)

    @transaction.atomic
    def update(
        self,
        sheet_id: int,
        employee_id: int,
        week_start: date,
        lines: list,
    ) -> FeuilleTemps:
        sheet = self.repository.get_for_employee_for_update(sheet_id, employee_id)
        if week_start != sheet.semaine_debut:
            raise ValidationError(
                {"semaine_debut": "La semaine d'une feuille existante ne peut pas être modifiée."}
            )
        if sheet.statut == StatutFeuilleTemps.SOUMISE:
            raise ValidationError(
                {"statut": "Une feuille soumise ne peut pas être modifiée avant décision."}
            )
        lines = self._normalize_lines(employee_id, lines)
        self._validate_lines(employee_id, sheet.semaine_debut, lines)
        if sheet.statut == StatutFeuilleTemps.VALIDEE:
            self.repository.set_status(sheet, StatutFeuilleTemps.BROUILLON)
        return self.repository.replace_lines(sheet, lines)

    @transaction.atomic
    def submit(self, sheet_id: int, employee_id: int) -> FeuilleTemps:
        sheet = self.repository.get_for_employee_for_update(sheet_id, employee_id)
        if sheet.statut != StatutFeuilleTemps.BROUILLON:
            raise ValidationError(
                {"statut": "Seule une feuille en brouillon peut être soumise."}
            )
        if not sheet.lignes.exists():
            raise ValidationError(
                {"lignes": "Ajoutez au moins une ligne avant de soumettre la feuille."}
            )
        self._validate_lines(
            employee_id,
            sheet.semaine_debut,
            [
                {
                    "date_travail": line.date_travail,
                    "projet": line.projet,
                    "tache": line.tache,
                    "heures": line.heures,
                }
                for line in sheet.lignes.all()
            ],
        )
        return self.repository.set_status(sheet, StatutFeuilleTemps.SOUMISE)

    @transaction.atomic
    def approve(self, sheet_id: int, reviewer_id: int) -> FeuilleTemps:
        sheet = self._get_submitted_for_decision(sheet_id)
        return self.repository.record_decision(
            sheet,
            StatutFeuilleTemps.VALIDEE,
            reviewer_id,
            timezone.now(),
        )

    @transaction.atomic
    def reject(
        self,
        sheet_id: int,
        reviewer_id: int,
        reason: str,
    ) -> FeuilleTemps:
        reason = reason.strip()
        if not reason:
            raise ValidationError({"motif": "Le motif du refus est obligatoire."})
        sheet = self._get_submitted_for_decision(sheet_id)
        return self.repository.record_decision(
            sheet,
            StatutFeuilleTemps.BROUILLON,
            reviewer_id,
            timezone.now(),
            rejection_reason=reason,
        )

    def _get_submitted_for_decision(self, sheet_id: int) -> FeuilleTemps:
        sheet = self.repository.get_for_decision(sheet_id)
        if sheet.statut != StatutFeuilleTemps.SOUMISE:
            raise ValidationError(
                {"statut": "Seule une feuille soumise peut faire l'objet d'une décision."}
            )
        return sheet

    @transaction.atomic
    def delete(self, sheet_id: int, employee_id: int) -> None:
        sheet = self.repository.get_for_employee_for_update(sheet_id, employee_id)
        if sheet.statut != StatutFeuilleTemps.BROUILLON:
            raise ValidationError(
                {"statut": "Seule une feuille en brouillon peut être supprimée."}
            )
        self.repository.delete(sheet)

    def _normalize_lines(self, employee_id, lines):
        normalized = []
        for line in lines:
            value = dict(line)
            if "jours" in value:
                hours = self._daily_hours(employee_id, value["date_travail"]) * value.pop("jours")
                value["heures"] = hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if value["heures"] < Decimal("0.01"):
                    raise ValidationError({"jours": "La fraction de journée doit représenter au moins 0,01 heure."})
            normalized.append(value)
        return normalized

    def _daily_hours(self, employee_id, work_date):
        contracts = list(self.repository.contracts_for_date(employee_id, work_date))
        if not contracts:
            raise ValidationError({"heures": f"Aucun contrat ne couvre la journée du {work_date}."})
        if len(contracts) > 1:
            raise ValidationError({"heures": f"Plusieurs contrats couvrent la journée du {work_date}; l'horaire journalier ne peut pas être déterminé."})
        hours = contracts[0].heures_journalieres
        if hours is None:
            raise ValidationError({"heures": f"L'horaire journalier du contrat n'est pas renseigné pour le {work_date}."})
        return hours

    def _validate_lines(
        self,
        employee_id: int,
        week_start: date,
        lines: list,
    ) -> None:
        daily_totals = defaultdict(lambda: Decimal("0.00"))
        for line in lines:
            work_date = line["date_travail"]
            if not week_start <= work_date <= week_start + timedelta(days=6):
                raise ValidationError(
                    {
                        "lignes": (
                            f"La date {work_date} n'appartient pas à la semaine "
                            f"du {week_start}."
                        )
                    }
                )
            project = line["projet"]
            task = line["tache"]
            if not self.repository.has_project_assignment(employee_id, project.pk):
                raise ValidationError(
                    {
                        "projet": (
                            f"L'employé n'est pas affecté au projet {project.pk}."
                        )
                    }
                )
            if not self.repository.has_active_project_and_task(project.pk, task.pk):
                raise ValidationError(
                    {"tache": "La tâche doit être active et appartenir au projet actif indiqué."}
                )
            daily_totals[work_date] += line["heures"]

        for work_date, total in daily_totals.items():
            daily_hours = self._daily_hours(employee_id, work_date)
            if total > daily_hours:
                raise ValidationError(
                    {
                        "heures": (
                            f"Le total du {work_date} ({total} h) dépasse "
                            f"l'horaire contractuel ({daily_hours} h)."
                        )
                    }
                )

    @staticmethod
    def _validate_week(week_start: date) -> None:
        if week_start.weekday() != 0:
            raise ValidationError(
                {"semaine_debut": "La semaine doit commencer un lundi."}
            )
        if week_start > date.max - timedelta(days=6):
            raise ValidationError({"semaine_debut": "La semaine doit être entièrement comprise dans le calendrier disponible."})


feuille_temps_service = FeuilleTempsService(FeuilleTempsRepository())
