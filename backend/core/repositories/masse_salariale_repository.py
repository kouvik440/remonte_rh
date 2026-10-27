from core.interfaces.masse_salariale_repository import MasseSalarialeRepositoryInterface
from core.models import Paie
from core.models.enums import StatutPaie


class MasseSalarialeRepository(MasseSalarialeRepositoryInterface):
    """Read model for payroll analytics, isolated from payroll commands."""

    def payroll_analytics_rows(self, start_period: str, end_period: str, department_id=None):
        rows = Paie.objects.filter(
            periode__gte=start_period,
            periode__lte=end_period,
            statut__in=(StatutPaie.VALIDEE, StatutPaie.PAYE),
        )
        if department_id is not None:
            rows = rows.filter(
                detail_calcul__classification__departement__id=department_id
            )
        results = []
        for payroll in rows.order_by("periode", "pk"):
            classification = (payroll.detail_calcul or {}).get("classification") or {}
            payroll.analytics_classification_available = bool(classification)
            department = classification.get("departement")
            payroll.analytics_department_id = department.get("id") if department else None
            payroll.analytics_department_name = (
                department.get("nom") if department else (
                    "Sans département" if payroll.analytics_classification_available else "Historique indisponible"
                )
            )
            payroll.analytics_contract_types = classification.get("types_contrat")
            results.append(payroll)
        return results
