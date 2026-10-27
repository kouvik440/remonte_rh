from django.db.models import QuerySet
from django.db.models import Q

from core.interfaces.contrat_repository import ContratRepositoryInterface
from core.models import Contrat


class ContratRepository(ContratRepositoryInterface):
    def all(self, employee_id: int = None) -> QuerySet:
        contracts = Contrat.objects.select_related("employe", "poste").prefetch_related("type").all()
        return contracts.filter(employe_id=employee_id) if employee_id is not None else contracts

    def for_employee_period(
        self,
        employee_id: int,
        date_debut,
        date_fin,
    ) -> QuerySet:
        return Contrat.objects.filter(
            employe_id=employee_id,
            date_debut__lte=date_fin,
        ).filter(Q(date_fin__isnull=True) | Q(date_fin__gte=date_debut)).prefetch_related("type").order_by(
            "-date_debut",
            "-pk",
        )

    def get(self, contrat_id: int) -> Contrat:
        return Contrat.objects.select_related("poste").prefetch_related("type").get(pk=contrat_id)

    def create(self, data: dict) -> Contrat:
        type_contrats = data.pop("type", [])
        contrat = Contrat.objects.create(**data)
        if type_contrats:
            contrat.type.set(type_contrats)
        return contrat

    def update(self, contrat: Contrat, data: dict) -> Contrat:
        type_contrats = data.pop("type", None)
        for field, value in data.items():
            setattr(contrat, field, value)
        contrat.save()
        if type_contrats is not None:
            contrat.type.set(type_contrats)
        return contrat

    def delete(self, contrat: Contrat) -> None:
        contrat.delete()
