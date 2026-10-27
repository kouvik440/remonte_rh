from collections import defaultdict
from decimal import Decimal

from rest_framework.exceptions import ValidationError

from core.models.enums import StatutPaie
from core.interfaces.masse_salariale_repository import MasseSalarialeRepositoryInterface
from core.repositories.masse_salariale_repository import MasseSalarialeRepository


ZERO = Decimal("0")
INCLUDED_STATUSES = (StatutPaie.VALIDEE, StatutPaie.PAYE)


class MasseSalarialeService:
    """Read-only aggregations over finalized payroll calculation snapshots."""

    def __init__(self, paie_repository: MasseSalarialeRepositoryInterface):
        self.paie_repository = paie_repository

    def summarize(self, start_period: str, end_period: str, department_id=None):
        self._validate_period(start_period, "periode_debut")
        self._validate_period(end_period, "periode_fin")
        if start_period > end_period:
            raise ValidationError({"periode_fin": "La fin doit être égale ou postérieure au début."})

        rows = self.paie_repository.payroll_analytics_rows(
            start_period, end_period, department_id=department_id
        )

        summary = self._new_totals()
        by_period = defaultdict(self._new_totals)
        by_year = defaultdict(self._new_totals)
        by_department = defaultdict(self._new_totals)
        by_contract_type = defaultdict(self._new_totals)
        employee_count_by_period = defaultdict(set)
        employee_count_by_year = defaultdict(set)

        for payroll in rows:
            department_key = (
                str(payroll.analytics_department_id)
                if payroll.analytics_department_id
                else "sans_departement" if payroll.analytics_classification_available
                else "historique_indisponible"
            )
            department_label = payroll.analytics_department_name
            contract_types = payroll.analytics_contract_types

            self._add_payroll(summary, payroll)
            self._add_payroll(by_period[payroll.periode], payroll)
            employee_count_by_period[payroll.periode].add(payroll.employe_id)
            year = payroll.periode[:4]
            self._add_payroll(by_year[year], payroll)
            employee_count_by_year[year].add(payroll.employe_id)
            self._add_payroll(
                by_department[(department_key, department_label)], payroll
            )
            if contract_types:
                for contract_type in contract_types:
                    self._add_payroll(
                        by_contract_type[(str(contract_type["id"]), contract_type["type"])],
                        payroll,
                    )
            else:
                label = (
                    "Sans type de contrat"
                    if payroll.analytics_classification_available
                    else "Historique indisponible"
                )
                key = "sans_type" if payroll.analytics_classification_available else "historique_indisponible"
                self._add_payroll(by_contract_type[(key, label)], payroll)

        return {
            "periode_debut": start_period,
            "periode_fin": end_period,
            "statuts_inclus": list(INCLUDED_STATUSES),
            "totaux": self._serialize_totals(summary),
            "evolution_mensuelle": self._period_rows(by_period, employee_count_by_period, "periode"),
            "evolution_annuelle": self._period_rows(by_year, employee_count_by_year, "annee"),
            "par_departement": [
                {"departement_id": key, "departement": label, **self._serialize_totals(value)}
                for (key, label), value in sorted(by_department.items(), key=lambda item: item[0][1])
            ],
            "par_type_contrat": [
                {"type_contrat_id": key, "type_contrat": label, **self._serialize_totals(value)}
                for (key, label), value in sorted(by_contract_type.items(), key=lambda item: item[0][1])
            ],
            "note_ventilation_contrat": (
                "Les ventilations utilisent le département et les types de contrat figés dans le snapshot "
                "au calcul. Pour les anciennes paies sans snapshot de classification, l'historique est "
                "indiqué comme indisponible. Une paie liée à plusieurs types est comptée dans chaque type ; "
                "les lignes par type ne sont alors pas additives."
            ),
        }

    def evolution(self, start_period: str, end_period: str, granularity="mensuelle", department_id=None):
        if granularity not in ("mensuelle", "annuelle"):
            raise ValidationError({"granularite": "Valeurs possibles : mensuelle ou annuelle."})
        summary = self.summarize(start_period, end_period, department_id=department_id)
        return {
            "periode_debut": start_period,
            "periode_fin": end_period,
            "granularite": granularity,
            "evolution": summary[f"evolution_{granularity}"],
        }

    @classmethod
    def _period_rows(cls, totals_by_period, employees_by_period, period_key):
        return [
            {period_key: period, "employes": len(employees_by_period[period]), **cls._serialize_totals(totals)}
            for period, totals in sorted(totals_by_period.items())
        ]

    @staticmethod
    def _new_totals():
        return {
            "paies_validees": 0,
            "paies_payees": 0,
            "brut_valide": ZERO,
            "net_valide": ZERO,
            "cotisations_validees": ZERO,
            "cout_employeur_valide": ZERO,
            "brut_paye": ZERO,
            "net_paye": ZERO,
            "cotisations_payees": ZERO,
            "cout_employeur_paye": ZERO,
        }

    @staticmethod
    def _amount(value):
        return Decimal(str(value or "0"))

    @classmethod
    def _add_payroll(cls, totals, payroll):
        if payroll.statut == StatutPaie.PAYE:
            totals["paies_payees"] += 1
            totals["brut_paye"] += cls._amount(payroll.salaire_brut)
            totals["net_paye"] += cls._amount(payroll.salaire_net)
            totals["cotisations_payees"] += cls._amount(payroll.cotisations)
            totals["cout_employeur_paye"] += cls._amount(payroll.cout_charge)
        else:
            totals["paies_validees"] += 1
            totals["brut_valide"] += cls._amount(payroll.salaire_brut)
            totals["net_valide"] += cls._amount(payroll.salaire_net)
            totals["cotisations_validees"] += cls._amount(payroll.cotisations)
            totals["cout_employeur_valide"] += cls._amount(payroll.cout_charge)

    @staticmethod
    def _serialize_totals(totals):
        return {
            key: (str(value.quantize(Decimal("0.01"))) if isinstance(value, Decimal) else value)
            for key, value in totals.items()
        }

    @staticmethod
    def _validate_period(value, field):
        try:
            year_text, month_text = value.split("-")
            year, month = int(year_text), int(month_text)
            if len(year_text) != 4 or len(month_text) != 2 or not 1 <= month <= 12:
                raise ValueError
        except (AttributeError, ValueError):
            raise ValidationError({field: "La période doit respecter le format AAAA-MM."})


masse_salariale_service = MasseSalarialeService(MasseSalarialeRepository())
