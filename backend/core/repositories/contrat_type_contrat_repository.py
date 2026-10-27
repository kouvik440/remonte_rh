from django.db.models import QuerySet

from core.interfaces.contrat_type_contrat_repository import ContratTypeContratRepositoryInterface
from core.models import ContratTypeContrat


class ContratTypeContratRepository(ContratTypeContratRepositoryInterface):
    def all(self) -> QuerySet:
        return ContratTypeContrat.objects.select_related("contrat", "type_contrat").all()

    def get(self, contrat_type_contrat_id: int) -> ContratTypeContrat:
        return ContratTypeContrat.objects.get(pk=contrat_type_contrat_id)

    def create(self, data: dict) -> ContratTypeContrat:
        return ContratTypeContrat.objects.create(**data)

    def update(self, contrat_type_contrat: ContratTypeContrat, data: dict) -> ContratTypeContrat:
        for field, value in data.items():
            setattr(contrat_type_contrat, field, value)
        contrat_type_contrat.save()
        return contrat_type_contrat

    def delete(self, contrat_type_contrat: ContratTypeContrat) -> None:
        contrat_type_contrat.delete()
