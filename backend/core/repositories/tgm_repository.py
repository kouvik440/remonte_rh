from django.db.models import Q

from core.interfaces.tgm_repository import TgmRepositoryInterface
from core.models import Contrat, Paie
from core.models.enums import StatutPaie


class TgmRepository(TgmRepositoryInterface):
    def finalized_payroll_rows(self, start_period: str, end_period: str) -> list:
        return list(
            Paie.objects.filter(
                periode__gte=start_period,
                periode__lte=end_period,
                statut__in=(StatutPaie.VALIDEE, StatutPaie.PAYE),
            )
            .select_related("employe")
            .order_by("employe_id", "periode", "pk")
        )

    def contracts_for_employees(self, employee_ids: list, start_date, end_date) -> list:
        if not employee_ids:
            return []
        return list(
            Contrat.objects.filter(
                employe_id__in=employee_ids,
                date_debut__lte=end_date,
            )
            .filter(Q(date_fin__isnull=True) | Q(date_fin__gte=start_date))
            .order_by("employe_id", "date_debut", "pk")
        )
