from datetime import date

from django.db.models import QuerySet
from django.db import transaction
from rest_framework.exceptions import ValidationError

from core.interfaces.contrat_repository import ContratRepositoryInterface
from core.models import Contrat
from core.repositories.contrat_repository import ContratRepository
from core.services.payroll_period import payroll_period_bounds
from .employe_history_service import record_change, contract_snapshot


class ContratService:
    def __init__(self, repository: ContratRepositoryInterface):
        self.repository = repository

    def get_all(self, employee_id: int = None) -> QuerySet:
        return self.repository.all(employee_id)

    def get_for_employee_period(
        self,
        employee_id: int,
        date_debut: date,
        date_fin: date,
    ) -> QuerySet:
        return self.repository.for_employee_period(employee_id, date_debut, date_fin)

    def get(self, contrat_id: int) -> Contrat:
        return self.repository.get(contrat_id)

    def payroll_context(self, employee_id: int, period: str) -> dict:
        start, end = payroll_period_bounds(period)
        contracts = list(self.get_for_employee_period(employee_id, start, end))
        state = "READY" if len(contracts) == 1 else "AMBIGUOUS" if contracts else "MISSING"
        return {"employe": employee_id, "periode": period, "state": state, "contracts": contracts}

    @transaction.atomic
    def create(self, data: dict, actor=None) -> Contrat:
        contract = self.repository.create(data)
        record_change(contract.employe_id, "CONTRAT", contract.pk, {}, contract_snapshot(contract), actor)
        record_change(contract.employe_id, "POSTE", contract.pk, {}, contract_snapshot(contract)["poste"], actor)
        return contract

    @transaction.atomic
    def update(self, contrat_id: int, data: dict, actor=None) -> Contrat:
        contrat = Contrat.objects.select_for_update().get(pk=contrat_id)
        before = contract_snapshot(contrat)
        if "employe" in data and data["employe"].pk != contrat.employe_id:
            raise ValidationError({"employe": "Un contrat ne peut pas être réaffecté à un autre employé."})
        contract = self.repository.update(contrat, data)
        after = contract_snapshot(contract)
        record_change(contract.employe_id, "CONTRAT", contract.pk, before, after, actor)
        record_change(contract.employe_id, "POSTE", contract.pk, before.get("poste", {}), after["poste"], actor)
        return contract

    @transaction.atomic
    def delete(self, contrat_id: int, actor=None) -> None:
        contrat = Contrat.objects.select_for_update().get(pk=contrat_id)
        record_change(contrat.employe_id, "CONTRAT", contrat.pk, contract_snapshot(contrat), {}, actor)
        record_change(contrat.employe_id, "POSTE", contrat.pk, contract_snapshot(contrat)["poste"], {}, actor)
        self.repository.delete(contrat)


contrat_service = ContratService(ContratRepository())
