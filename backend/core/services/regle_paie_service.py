from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from core.interfaces.regle_paie_repository import ReglePaieRepositoryInterface
from core.models import ReglePaie
from core.repositories.regle_paie_repository import ReglePaieRepository


class ReglePaieService:
    def __init__(self, repository: ReglePaieRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, regle_id: int) -> ReglePaie:
        return self.repository.get(regle_id)

    def for_period(self, date_debut, date_fin) -> QuerySet:
        return self.repository.for_period(date_debut, date_fin)

    def create(self, data: dict) -> ReglePaie:
        return self.repository.create(data)

    def update(self, regle_id: int, data: dict) -> ReglePaie:
        regle = self.repository.get(regle_id)
        if regle.valide:
            raise ValidationError({"valide": "Un profil validé est immuable."})
        return self.repository.update(regle, data)

    def validate(self, regle_id: int) -> ReglePaie:
        regle = self.repository.get(regle_id)
        if not regle.source_reference.strip():
            raise ValidationError(
                {"source_reference": "Une référence officielle est requise."}
            )
        return self.repository.update(regle, {"valide": True})

    def delete(self, regle_id: int) -> None:
        regle = self.repository.get(regle_id)
        if regle.valide:
            raise ValidationError({"valide": "Un profil validé ne peut pas être supprimé."})
        self.repository.delete(regle)


regle_paie_service = ReglePaieService(ReglePaieRepository())
