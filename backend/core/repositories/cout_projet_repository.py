from datetime import date

from django.db.models import QuerySet

from core.interfaces.cout_projet_repository import CoutProjetRepositoryInterface
from core.models import LigneFeuilleTemps
from core.models.enums import StatutFeuilleTemps


class CoutProjetRepository(CoutProjetRepositoryInterface):
    def validated_time_lines(
        self,
        start_date: date,
        end_date: date,
    ) -> QuerySet[LigneFeuilleTemps]:
        return LigneFeuilleTemps.objects.filter(
            feuille__statut=StatutFeuilleTemps.VALIDEE,
            date_travail__range=(start_date, end_date),
        ).select_related(
            "feuille",
            "feuille__employe",
            "projet",
            "tache",
        ).order_by(
            "projet__nom",
            "tache__nom",
            "date_travail",
            "pk",
        )
