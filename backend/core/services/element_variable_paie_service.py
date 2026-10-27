from django.db.models import QuerySet
from rest_framework.exceptions import ValidationError

from core.interfaces.element_variable_paie_repository import (
    ElementVariablePaieRepositoryInterface,
)
from core.models import ElementVariablePaie
from core.repositories.element_variable_paie_repository import (
    ElementVariablePaieRepository,
)


class ElementVariablePaieService:
    def __init__(self, repository: ElementVariablePaieRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def filtered(self, employee_id: int = None, periode: str = None) -> QuerySet:
        return self.repository.filtered(employee_id=employee_id, periode=periode)

    def get(self, element_id: int) -> ElementVariablePaie:
        return self.repository.get(element_id)

    def for_employee_period(self, employee_id: int, periode: str) -> QuerySet:
        return self.repository.for_employee_period(employee_id, periode)

    def create(self, data: dict) -> ElementVariablePaie:
        return self.repository.create(data)

    def update(self, element_id: int, data: dict) -> ElementVariablePaie:
        element = self.repository.get(element_id)
        if element.valide:
            raise ValidationError(
                {"valide": "Un élément validé est immuable."}
            )
        return self.repository.update(element, data)

    def validate(self, element_id: int) -> ElementVariablePaie:
        element = self.repository.get(element_id)
        if element.valide:
            raise ValidationError({"valide": "Cet élément est déjà validé."})
        return self.repository.update(element, {"valide": True})

    def delete(self, element_id: int) -> None:
        element = self.repository.get(element_id)
        if element.valide:
            raise ValidationError(
                {"valide": "Un élément validé ne peut pas être supprimé."}
            )
        self.repository.delete(element)


element_variable_paie_service = ElementVariablePaieService(
    ElementVariablePaieRepository()
)