from django.db.models import Q, QuerySet

from core.interfaces.regle_paie_repository import ReglePaieRepositoryInterface
from core.models import ReglePaie


class ReglePaieRepository(ReglePaieRepositoryInterface):
    def all(self) -> QuerySet:
        return ReglePaie.objects.all()

    def get(self, regle_id: int) -> ReglePaie:
        return ReglePaie.objects.get(pk=regle_id)

    def for_period(self, date_debut, date_fin) -> QuerySet:
        return self.all().filter(actif=True, date_debut__lte=date_debut).filter(
            Q(date_fin__isnull=True) | Q(date_fin__gte=date_fin)
        )

    def create(self, data: dict) -> ReglePaie:
        return ReglePaie.objects.create(**data)

    def update(self, regle: ReglePaie, data: dict) -> ReglePaie:
        for field, value in data.items():
            setattr(regle, field, value)
        regle.save()
        return regle

    def delete(self, regle: ReglePaie) -> None:
        regle.delete()
