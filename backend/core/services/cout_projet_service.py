from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from rest_framework.exceptions import ValidationError

from core.repositories.cout_projet_repository import CoutProjetRepository
from core.services.tgm_service import tgm_service


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


class CoutProjetService:
    def __init__(self, repository, tgm_calculator):
        self.repository = repository
        self.tgm_calculator = tgm_calculator

    def summarize(self, start_date: date, end_date: date) -> dict:
        lines = list(self.repository.validated_time_lines(start_date, end_date))
        hourly_rates = self._hourly_rates(lines)
        totals = self._new_totals()
        projects = {}
        reconciliation = {}

        for line in lines:
            project = projects.setdefault(
                line.projet_id,
                {
                    "projet_id": line.projet_id,
                    "projet_code": line.projet.code,
                    "projet_nom": line.projet.nom,
                    **self._new_totals(),
                    "taches": {},
                    "employes": {},
                },
            )
            task = project["taches"].setdefault(
                line.tache_id,
                {
                    "tache_id": line.tache_id,
                    "tache_code": line.tache.code,
                    "tache_nom": line.tache.nom,
                    **self._new_totals(),
                },
            )
            employee = project["employes"].setdefault(
                line.feuille.employe_id,
                {
                    "employe_id": line.feuille.employe_id,
                    "matricule": line.feuille.employe.matricule,
                    "employe_nom": line.feuille.employe.nom,
                    "employe_prenom": line.feuille.employe.prenom,
                    **self._new_totals(),
                },
            )
            period = f"{line.date_travail.year:04d}-{line.date_travail.month:02d}"
            rate = hourly_rates.get((line.feuille.employe_id, line.date_travail.year, line.date_travail.month))
            detail = reconciliation.setdefault((line.projet_id, line.feuille.employe_id, period), {
                "projet_id": line.projet_id, "projet_code": line.projet.code, "projet_nom": line.projet.nom,
                "employe_id": line.feuille.employe_id, "employe_nom": line.feuille.employe.nom,
                "employe_prenom": line.feuille.employe.prenom, "matricule": line.feuille.employe.matricule,
                "periode": period, "taux_horaire_charge": self._format(rate) if rate is not None else None,
                **self._new_totals(),
            })
            self._add_line(detail, line, hourly_rates)
            self._add_line(project, line, hourly_rates)
            self._add_line(employee, line, hourly_rates)
            self._add_line(task, line, hourly_rates)
            self._add_line(totals, line, hourly_rates)

        project_rows = self._serialize_projects(projects)
        return {
            "date_debut": start_date.isoformat(),
            "date_fin": end_date.isoformat(),
            "formule": "Coût chargé mensuel / heures prévisionnelles du mois × heures validées",
            "devise": "XOF",
            "statuts_feuille_inclus": ["VALIDEE"],
            "totaux": self._serialize_totals(totals),
            "projets": project_rows,
            "rapprochement": [
                {**{key: value for key, value in row.items() if key not in self._new_totals()}, **self._serialize_totals(row)}
                for row in sorted(reconciliation.values(), key=lambda item: (item["projet_nom"], item["employe_nom"], item["employe_id"], item["periode"]))
            ],
            "note": (
                "Il s'agit d'une estimation basée sur le TGM chargé mensuel et les heures "
                "validées. Les heures sans TGM disponible restent visibles et ne sont pas "
                "présentées comme un coût complet. Les taux horaires suivent les contrats, sans diviseur fixe. "
                "Seules les paies en XOF sont chiffrées ; les autres devises restent sans taux, sans conversion implicite. "
                "Le chiffre d'affaires d'une simulation est saisi séparément et n'est pas enregistré."
            ),
        }

    def simulate(self, start_date, end_date, project_id, revenue):
        report = self.summarize(start_date, end_date)
        project = next((row for row in report["projets"] if row["projet_id"] == project_id), None)
        if project is None:
            raise ValidationError({"projet": "Aucune heure validée pour ce projet sur la période sélectionnée."})
        cost = Decimal(project["cout_estime"]) if project["cout_estime"] is not None else None
        margin = revenue - cost if cost is not None else None
        return {
            "date_debut": report["date_debut"], "date_fin": report["date_fin"],
            "projet_id": project_id, "projet_nom": project["projet_nom"], "devise": "XOF",
            "chiffre_affaires": self._format(revenue), **self._serialize_totals_from_project(project),
            "marge_personnel": self._format(margin) if margin is not None else None,
            "taux_marge_personnel": self._format(margin / revenue * Decimal("100")) if margin is not None and revenue > ZERO else None,
            "note": "Simulation non enregistrée. La marge soustrait uniquement le coût estimé du personnel du chiffre d'affaires saisi ; elle exclut les autres charges du projet. Le pourcentage n'est pas défini lorsque le chiffre d'affaires est nul.",
        }

    @staticmethod
    def _serialize_totals_from_project(project):
        return {key: project[key] for key in ("heures_validees", "heures_sans_tgm", "cout_calculable", "cout_estime", "cout_complet")}

    def _hourly_rates(self, lines: list) -> dict:
        periods = {
            (line.date_travail.year, line.date_travail.month)
            for line in lines
        }
        rate_by_employee_period = {}
        for year, month in periods:
            period = f"{year:04d}-{month:02d}"
            report = self.tgm_calculator.calculate(period, period)
            for row in report["employes"]:
                hours, cost = row["heures_previsionnelles"], row["cout_charge_total"]
                rate_by_employee_period[(row["employe_id"], year, month)] = (
                    Decimal(cost) / Decimal(hours)
                    if row["devise"] == "XOF" and cost is not None and hours is not None and Decimal(hours) > ZERO
                    else None
                )
        return rate_by_employee_period

    @classmethod
    def _add_line(cls, totals: dict, line, hourly_rates: dict) -> None:
        hours = line.heures
        totals["heures_validees"] += hours
        hourly_rate = hourly_rates.get(
            (line.feuille.employe_id, line.date_travail.year, line.date_travail.month)
        )
        if hourly_rate is None:
            totals["heures_sans_taux"] += hours
            return
        totals["cout_calculable"] += hours * hourly_rate

    @staticmethod
    def _new_totals() -> dict:
        return {
            "heures_validees": ZERO,
            "heures_sans_taux": ZERO,
            "cout_calculable": ZERO,
        }

    @classmethod
    def _serialize_totals(cls, totals: dict) -> dict:
        hours = totals["heures_validees"]
        unpriced_hours = totals["heures_sans_taux"]
        calculated_cost = totals["cout_calculable"].quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )
        return {
            "heures_validees": cls._format(hours),
            "heures_sans_tgm": cls._format(unpriced_hours),
            "cout_calculable": cls._format(calculated_cost),
            "cout_estime": (
                None if unpriced_hours > ZERO else cls._format(calculated_cost)
            ),
            "cout_complet": unpriced_hours == ZERO,
        }

    @classmethod
    def _serialize_projects(cls, projects: dict) -> list:
        serialized = []
        for project in projects.values():
            tasks = sorted(
                project["taches"].values(),
                key=lambda task: task["tache_nom"].casefold(),
            )
            serialized.append(
                {
                    "projet_id": project["projet_id"],
                    "projet_code": project["projet_code"],
                    "projet_nom": project["projet_nom"],
                    **cls._serialize_totals(project),
                    "employes": [
                        {
                            "employe_id": employee["employe_id"],
                            "matricule": employee["matricule"],
                            "employe_nom": employee["employe_nom"],
                            "employe_prenom": employee["employe_prenom"],
                            **cls._serialize_totals(employee),
                        }
                        for employee in sorted(project["employes"].values(), key=lambda item: (item["employe_nom"], item["employe_prenom"], item["employe_id"]))
                    ],
                    "taches": [
                        {
                            "tache_id": task["tache_id"],
                            "tache_code": task["tache_code"],
                            "tache_nom": task["tache_nom"],
                            **cls._serialize_totals(task),
                        }
                        for task in tasks
                    ],
                }
            )
        return sorted(
            serialized,
            key=lambda project: project["projet_nom"].casefold(),
        )

    @staticmethod
    def _format(value: Decimal) -> str:
        return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


cout_projet_service = CoutProjetService(
    CoutProjetRepository(),
    tgm_service,
)
