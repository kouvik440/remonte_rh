from django.db.models import QuerySet
from django.db import transaction

from core.interfaces.contrat_type_contrat_repository import ContratTypeContratRepositoryInterface
from core.models import ContratTypeContrat, Contrat
from .employe_history_service import contract_snapshot, record_change
from core.repositories.contrat_type_contrat_repository import ContratTypeContratRepository


class ContratTypeContratService:
    def __init__(self, repository: ContratTypeContratRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, contrat_type_contrat_id: int) -> ContratTypeContrat:
        return self.repository.get(contrat_type_contrat_id)

    @transaction.atomic
    def create(self, data: dict, actor=None) -> ContratTypeContrat:
        contract = Contrat.objects.select_for_update().get(pk=data["contrat"].pk)
        before = contract_snapshot(contract)
        link = self.repository.create(data)
        record_change(contract.employe_id, "CONTRAT", contract.pk, before, contract_snapshot(contract), actor)
        return link

    @transaction.atomic
    def update(self, contrat_type_contrat_id: int, data: dict, actor=None) -> ContratTypeContrat:
        contrat_type_contrat = self.repository.get(contrat_type_contrat_id)
        ids = {contrat_type_contrat.contrat_id, data.get("contrat", contrat_type_contrat.contrat).pk}
        contracts = list(Contrat.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
        before = {item.pk: contract_snapshot(item) for item in contracts}
        link = self.repository.update(contrat_type_contrat, data)
        for contract in contracts:
            record_change(contract.employe_id, "CONTRAT", contract.pk, before[contract.pk], contract_snapshot(contract), actor)
        return link

    @transaction.atomic
    def delete(self, contrat_type_contrat_id: int, actor=None) -> None:
        contrat_type_contrat = self.repository.get(contrat_type_contrat_id)
        contract = Contrat.objects.select_for_update().get(pk=contrat_type_contrat.contrat_id)
        before = contract_snapshot(contract)
        self.repository.delete(contrat_type_contrat)
        record_change(contract.employe_id, "CONTRAT", contract.pk, before, contract_snapshot(contract), actor)


contrat_type_contrat_service = ContratTypeContratService(
    ContratTypeContratRepository()
)
