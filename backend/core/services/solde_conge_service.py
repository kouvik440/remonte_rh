from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from core.interfaces.solde_conge_repository import SoldeCongeRepositoryInterface
from core.models import SoldeConge
from core.repositories.solde_conge_repository import SoldeCongeRepository
from rest_framework.exceptions import ValidationError


class SoldeCongeService:
    def __init__(self, repository: SoldeCongeRepositoryInterface):
        self.repository = repository

    def get_balances(self, year: int, employee_id: Optional[int] = None) -> list:
        balances = self.repository.entitlements(year, employee_id)

        days_used = self._group_working_dates(
            self.repository.approved_absences(year, employee_id), year
        )
        days_pending = self._group_working_dates(
            self.repository.pending_absences(year, employee_id), year
        )
        return [
            self._serialize_balance(
                balance,
                days_used[(balance.employe_id, balance.type_conge_id)],
                days_pending[(balance.employe_id, balance.type_conge_id)],
            )
            for balance in balances
        ]

    def _group_working_dates(self, absences, year: int) -> dict:
        dates_by_employee_type = defaultdict(set)
        for absence in absences:
            dates_by_employee_type[(absence.employe_id, absence.type_conge_id)].update(
                self._get_used_dates([absence], year)
            )
        return dates_by_employee_type

    @staticmethod
    def _serialize_balance(balance, used_dates: set, pending_dates: set) -> dict:
        used_days = len(used_dates)
        pending_days = len(pending_dates - used_dates)
        annual_quota = balance.type_conge.jours_par_annee if balance.type_conge else 0
        return {
            "id": balance.pk,
            "employe": balance.employe_id,
            "employe_nom": balance.employe.nom,
            "employe_prenom": balance.employe.prenom,
            "employe_matricule": balance.employe.matricule,
            "type_conge": balance.type_conge_id,
            "type_conge_libelle": balance.type_conge.libelle if balance.type_conge else "",
            "type_conge_code": balance.type_conge.code if balance.type_conge else "",
            "annee": balance.annee,
            "acquis": annual_quota,
            "pris": used_days,
            "restant": annual_quota - used_days,
            "en_attente": pending_days,
            "disponible": annual_quota - used_days - pending_days,
        }

    def validate_request_quota(
        self,
        employee_id: int,
        leave_type,
        date_start: date,
        date_end: date,
        exclude_request_id: int = None,
    ) -> None:
        """Reserve weekdays from an employee's annual allowance for this request."""
        self.repository.lock_employee(employee_id)
        for year in range(date_start.year, date_end.year + 1):
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            requested_dates = self._working_dates(
                max(date_start, year_start),
                min(date_end, year_end),
            )
            if not requested_dates:
                continue

            balance = self.repository.get_for_employee_type_year(
                employee_id,
                leave_type.pk,
                year,
            )
            quota = leave_type.jours_par_annee
            if quota <= 0:
                raise ValidationError(
                    {"date_fin": f"Aucun quota annuel positif n'est configuré pour {leave_type.code} en {year}."}
                )

            reserved_absences = self.repository.reserved_absences(
                employee_id,
                leave_type.pk,
                year,
                exclude_id=exclude_request_id,
            )
            reserved_dates = self._get_used_dates(reserved_absences, year)

            total_reserved = len(reserved_dates | requested_dates)
            if total_reserved > quota:
                raise ValidationError(
                    {"date_fin": (
                        f"Le quota {leave_type.code} de {year} est de {quota} jour(s); "
                        f"cette demande porterait les jours utilisés ou réservés à {total_reserved}."
                    )}
                )

            if balance is None:
                self.repository.create({
                    "employe_id": employee_id,
                    "type_conge_id": leave_type.pk,
                    "annee": year,
                    "acquis": quota,
                    "pris": 0,
                })

    def refresh_balance(
        self,
        employee_id: int,
        leave_type_id: int,
        year: int,
    ) -> Optional[SoldeConge]:
        balance = self.repository.get_for_employee_type_year(
            employee_id, leave_type_id, year
        )
        if balance is None:
            return None

        absences = self.repository.approved_absences(
            year, employee_id, leave_type_id=leave_type_id
        )
        used_dates = self._get_used_dates(absences, year)
        return self.repository.update_used_days(balance, len(used_dates))

    def _get_used_dates(self, absences, year: int) -> set:
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        used_dates = set()
        for absence in absences:
            start_date = max(absence.date_debut, year_start)
            end_date = min(absence.date_fin, year_end)
            used_dates.update(self._working_dates(start_date, end_date))
        return used_dates

    @staticmethod
    def _working_dates(start_date: date, end_date: date) -> set:
        if end_date < start_date:
            return set()
        working_dates = set()
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:
                working_dates.add(current_date)
            current_date += timedelta(days=1)
        return working_dates


solde_conge_service = SoldeCongeService(SoldeCongeRepository())
