import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from rest_framework.exceptions import ValidationError

from core.models.enums import StatutPaie
from core.interfaces.tgm_repository import TgmRepositoryInterface
from core.repositories.tgm_repository import TgmRepository


ZERO = Decimal("0")
CENT = Decimal("0.01")
INCLUDED_STATUSES = (StatutPaie.VALIDEE, StatutPaie.PAYE)


class TgmService:
    """Calculates planned-workday gross and employer-cost averages per employee."""

    def __init__(self, repository: TgmRepositoryInterface):
        self.repository = repository

    def calculate(self, start_period: str, end_period: str) -> dict:
        self._validate_period(start_period, "periode_debut")
        self._validate_period(end_period, "periode_fin")
        if start_period > end_period:
            raise ValidationError(
                {"periode_fin": "La période de fin doit être égale ou postérieure au début."}
            )

        payrolls = self.repository.finalized_payroll_rows(start_period, end_period)
        periods = {payroll.periode for payroll in payrolls}
        contracts = self.repository.contracts_for_employees(
            list({payroll.employe_id for payroll in payrolls}),
            self._first_day(start_period),
            self._last_day(end_period),
        )
        contracts_by_employee = defaultdict(list)
        for contract in contracts:
            contracts_by_employee[contract.employe_id].append(contract)

        grouped = {}
        for payroll in payrolls:
            key = (payroll.employe_id, payroll.devise)
            if key not in grouped:
                grouped[key] = {
                    "employe": payroll.employe,
                    "devise": payroll.devise,
                    "periodes": set(),
                    "paies_validees": 0,
                    "paies_payees": 0,
                    "salaire_brut": ZERO,
                    "cout_charge": ZERO,
                    "salaire_brut_complet": True,
                    "cout_charge_complet": True,
                    "jours_previsionnels": set(),
                    "heures_par_jour": {},
                    "periodes_sans_jours": set(),
                }

            entry = grouped[key]
            entry["periodes"].add(payroll.periode)
            if payroll.statut == StatutPaie.PAYE:
                entry["paies_payees"] += 1
            else:
                entry["paies_validees"] += 1

            if payroll.salaire_brut is None:
                entry["salaire_brut_complet"] = False
            else:
                entry["salaire_brut"] += payroll.salaire_brut
            if payroll.cout_charge is None:
                entry["cout_charge_complet"] = False
            else:
                entry["cout_charge"] += payroll.cout_charge

            month_start, month_end = self._period_bounds(payroll.periode)
            employee = payroll.employe
            employment_end = employee.date_sortie or month_end
            period_start = max(month_start, employee.date_entree)
            period_end = min(month_end, employment_end)
            covered_days = 0
            for day in self._working_dates(period_start, period_end):
                active_contracts = [
                    contract for contract in contracts_by_employee[payroll.employe_id]
                    if contract.date_debut <= day
                    and (contract.date_fin is None or contract.date_fin >= day)
                ]
                if active_contracts:
                    covered_days += 1
                    entry["jours_previsionnels"].add(day)
                    hours = active_contracts[0].heures_journalieres if len(active_contracts) == 1 else None
                    entry["heures_par_jour"][day] = hours if hours is not None and hours > ZERO else None
            if not covered_days:
                entry["periodes_sans_jours"].add(payroll.periode)

        employee_rows = [
            self._serialize_employee(entry)
            for entry in grouped.values()
        ]
        employee_rows.sort(
            key=lambda row: (
                row["employe_nom"].casefold(),
                row["employe_prenom"].casefold(),
                row["devise"],
            )
        )
        return {
            "periode_debut": start_period,
            "periode_fin": end_period,
            "periodes_avec_paie": sorted(periods),
            "statuts_inclus": list(INCLUDED_STATUSES),
            "base_jours": "jours ouvrés (lundi-vendredi) couverts par un contrat",
            "employes": employee_rows,
            "note": (
                "Les taux sont des moyennes calculées sur les jours ouvrés prévus couverts par un contrat "
                "pour les périodes ayant une paie validée ou payée. Ils ne représentent pas un pointage "
                "réel ni un coût imputé à un projet. Les jours fériés ne sont pas déduits. "
                "Les heures prévues utilisent les heures journalières des contrats actuellement enregistrés ; "
                "un horaire absent ou plusieurs contrats sur un même jour rendent le taux horaire indisponible. "
                "Les mois sans paie finalisée sont exclus ; les modifications de contrats peuvent changer ces estimations."
            ),
        }

    @classmethod
    def _serialize_employee(cls, entry: dict) -> dict:
        planned_days = len(entry["jours_previsionnels"])
        days_complete = planned_days > 0 and not entry["periodes_sans_jours"]
        hours_available = days_complete and all(hours is not None for hours in entry["heures_par_jour"].values())
        planned_hours = sum(entry["heures_par_jour"].values(), ZERO) if hours_available else None
        gross_total = (
            entry["salaire_brut"] if entry["salaire_brut_complet"] else None
        )
        employer_cost_total = (
            entry["cout_charge"] if entry["cout_charge_complet"] else None
        )
        return {
            "employe_id": entry["employe"].pk,
            "matricule": entry["employe"].matricule,
            "employe_nom": entry["employe"].nom,
            "employe_prenom": entry["employe"].prenom,
            "devise": entry["devise"],
            "periodes": sorted(entry["periodes"]),
            "paies_validees": entry["paies_validees"],
            "paies_payees": entry["paies_payees"],
            "jours_ouvres_previsionnels": planned_days,
            "periodes_sans_jours": sorted(entry["periodes_sans_jours"]),
            "heures_previsionnelles": cls._format_amount(planned_hours),
            "salaire_brut_total": cls._format_amount(gross_total),
            "cout_charge_total": cls._format_amount(employer_cost_total),
            "taux_journalier_brut": cls._rate(gross_total, planned_days if days_complete else 0),
            "taux_journalier_charge": cls._rate(employer_cost_total, planned_days if days_complete else 0),
            "taux_horaire_brut": cls._rate(gross_total, planned_hours or 0),
            "taux_horaire_charge": cls._rate(employer_cost_total, planned_hours or 0),
            "motif_indisponibilite_horaire": None if hours_available else (
                "Aucun horaire complet et non ambigu : renseignez les heures journalières et vérifiez les contrats couvrant la période."
            ),
            "motif_indisponibilite": cls._unavailable_reason(
                days_complete,
                entry["salaire_brut_complet"],
                entry["cout_charge_complet"],
            ),
        }

    @staticmethod
    def _rate(amount, denominator):
        if amount is None or denominator == 0:
            return None
        return str((amount / Decimal(denominator)).quantize(CENT, rounding=ROUND_HALF_UP))

    @staticmethod
    def _format_amount(amount):
        if amount is None:
            return None
        return str(amount.quantize(CENT, rounding=ROUND_HALF_UP))

    @staticmethod
    def _unavailable_reason(days_complete, gross_complete, employer_cost_complete):
        reasons = []
        if not days_complete:
            reasons.append("Au moins une période avec paie ne comporte aucun jour ouvré couvert par un contrat.")
        if not gross_complete:
            reasons.append("Le salaire brut manque pour au moins une paie incluse.")
        if not employer_cost_complete:
            reasons.append("Le coût chargé manque pour au moins une paie incluse.")
        return " ".join(reasons) or None

    @staticmethod
    def _period_bounds(period: str):
        year, month = map(int, period.split("-"))
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])

    @classmethod
    def _first_day(cls, period: str):
        return cls._period_bounds(period)[0]

    @classmethod
    def _last_day(cls, period: str):
        return cls._period_bounds(period)[1]

    @staticmethod
    def _working_dates(start_date: date, end_date: date):
        if end_date < start_date:
            return
        for ordinal in range(start_date.toordinal(), end_date.toordinal() + 1):
            current = date.fromordinal(ordinal)
            if current.weekday() < 5:
                yield current

    @staticmethod
    def _validate_period(value: str, field: str):
        try:
            year_text, month_text = value.split("-")
            year, month = int(year_text), int(month_text)
            if (
                len(year_text) != 4
                or len(month_text) != 2
                or not 1 <= month <= 12
            ):
                raise ValueError
            date(year, month, 1)
        except (AttributeError, TypeError, ValueError):
            raise ValidationError({field: "La période doit respecter le format AAAA-MM."})


tgm_service = TgmService(TgmRepository())
