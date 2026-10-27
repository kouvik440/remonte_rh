from abc import ABC, abstractmethod
from datetime import date

from django.db.models import QuerySet

from core.models import LigneFeuilleTemps

class CoutProjetRepositoryInterface(ABC):
    @abstractmethod
    def validated_time_lines(
        self,
        start_date: date,
        end_date: date,
    ) -> QuerySet[LigneFeuilleTemps]:
        raise NotImplementedError
