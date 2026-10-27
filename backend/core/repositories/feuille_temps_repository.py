from django.db.models import Prefetch, Q, QuerySet

from core.interfaces.feuille_temps_repository import FeuilleTempsRepositoryInterface
from core.models import (
    AffectationProjet,
    Contrat,
    FeuilleTemps,
    LigneFeuilleTemps,
    Projet,
    TacheProjet,
)
from core.models.enums import StatutFeuilleTemps


class FeuilleTempsRepository(FeuilleTempsRepositoryInterface):
    def for_employee(
        self,
        employee_id: int,
        week_start=None,
        work_date=None,
    ) -> QuerySet:
        lines = LigneFeuilleTemps.objects.select_related(
            "projet",
            "tache",
        )
        sheets = FeuilleTemps.objects.filter(
            employe_id=employee_id,
        ).select_related(
            "employe",
            "valideur",
        ).prefetch_related(Prefetch("lignes", queryset=lines))
        if week_start is not None:
            sheets = sheets.filter(semaine_debut=week_start)
        if work_date is not None:
            sheets = sheets.filter(lignes__date_travail=work_date).distinct()
        return sheets

    def get_for_employee(self, sheet_id: int, employee_id: int) -> FeuilleTemps:
        return self.for_employee(employee_id).get(pk=sheet_id)

    def get_for_employee_for_update(self, sheet_id: int, employee_id: int) -> FeuilleTemps:
        return FeuilleTemps.objects.select_for_update().get(pk=sheet_id, employe_id=employee_id)

    def submitted_for_decision(self) -> QuerySet:
        lines = LigneFeuilleTemps.objects.select_related("projet", "tache")
        return FeuilleTemps.objects.filter(
            statut=StatutFeuilleTemps.SOUMISE,
        ).select_related(
            "employe",
            "valideur",
        ).prefetch_related(
            Prefetch("lignes", queryset=lines)
        )

    def active_projects_for_employee(self, employee_id: int, pending_only=False) -> QuerySet:
        active_tasks = TacheProjet.objects.filter(actif=True)
        if pending_only:
            validated_tasks = LigneFeuilleTemps.objects.filter(
                feuille__employe_id=employee_id,
                feuille__statut=StatutFeuilleTemps.VALIDEE,
            ).values("tache_id")
            active_tasks = active_tasks.exclude(pk__in=validated_tasks)
        projects = Projet.objects.filter(
            actif=True,
            affectations__employe_id=employee_id,
        )
        if pending_only:
            projects = projects.filter(taches__in=active_tasks)
        return projects.distinct().prefetch_related(
            Prefetch("taches", queryset=active_tasks)
        )

    def get_for_decision(self, sheet_id: int) -> FeuilleTemps:
        return FeuilleTemps.objects.select_for_update().get(pk=sheet_id)

    def create(self, employee_id: int, week_start):
        return FeuilleTemps.objects.get_or_create(
            employe_id=employee_id,
            semaine_debut=week_start,
        )

    def replace_lines(self, sheet: FeuilleTemps, lines: list) -> FeuilleTemps:
        sheet.lignes.all().delete()
        LigneFeuilleTemps.objects.bulk_create(
            [
                LigneFeuilleTemps(
                    feuille=sheet,
                    date_travail=line["date_travail"],
                    projet=line["projet"],
                    tache=line["tache"],
                    heures=line["heures"],
                    commentaire=line.get("commentaire", ""),
                )
                for line in lines
            ]
        )
        return self.get_for_employee(sheet.pk, sheet.employe_id)

    def set_status(self, sheet: FeuilleTemps, status: str) -> FeuilleTemps:
        sheet.statut = status
        update_fields = ["statut"]
        if status in {
            StatutFeuilleTemps.BROUILLON,
            StatutFeuilleTemps.SOUMISE,
        }:
            sheet.valideur = None
            sheet.date_decision = None
            sheet.motif_refus = ""
            update_fields.extend(["valideur", "date_decision", "motif_refus"])
        sheet.save(update_fields=update_fields)
        return self.get_for_employee(sheet.pk, sheet.employe_id)

    def record_decision(
        self,
        sheet: FeuilleTemps,
        status: str,
        reviewer_id: int,
        decided_at,
        rejection_reason: str = "",
    ) -> FeuilleTemps:
        sheet.statut = status
        sheet.valideur_id = reviewer_id
        sheet.date_decision = decided_at
        sheet.motif_refus = rejection_reason
        sheet.save(
            update_fields=[
                "statut",
                "valideur",
                "date_decision",
                "motif_refus",
            ]
        )
        return self.get_for_employee(sheet.pk, sheet.employe_id)

    def delete(self, sheet: FeuilleTemps) -> None:
        sheet.delete()

    def has_project_assignment(self, employee_id: int, project_id: int) -> bool:
        return AffectationProjet.objects.filter(
            employe_id=employee_id,
            projet_id=project_id,
        ).exists()

    def has_active_project_and_task(self, project_id: int, task_id: int) -> bool:
        return TacheProjet.objects.filter(
            pk=task_id,
            projet_id=project_id,
            actif=True,
            projet__actif=True,
        ).exists()

    def contracts_for_date(self, employee_id: int, work_date):
        return Contrat.objects.filter(
            employe_id=employee_id,
            date_debut__lte=work_date,
        ).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=work_date)
        )
