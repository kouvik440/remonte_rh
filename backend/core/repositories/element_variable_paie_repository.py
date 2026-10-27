from django.db.models import QuerySet

from core.interfaces.element_variable_paie_repository import (
    ElementVariablePaieRepositoryInterface,
)
from core.models import ElementVariablePaie


class ElementVariablePaieRepository(ElementVariablePaieRepositoryInterface):
    def all(self) -> QuerySet:
        return ElementVariablePaie.objects.select_related("employe").all()

    def filtered(self, employee_id: int = None, periode: str = None) -> QuerySet:
        elements = self.all()
        if employee_id is not None:
            elements = elements.filter(employe_id=employee_id)
        if periode is not None:
            elements = elements.filter(periode=periode)
        return elements

    def get(self, element_id: int) -> ElementVariablePaie:
        return ElementVariablePaie.objects.select_related("employe").get(pk=element_id)

    def for_employee_period(self, employee_id: int, periode: str) -> QuerySet:
        return self.all().filter(
            employe_id=employee_id,
            periode=periode,
            valide=True,
        ).order_by("pk")

    def create(self, data: dict) -> ElementVariablePaie:
        return ElementVariablePaie.objects.create(**data)

    def update(
        self,
        element: ElementVariablePaie,
        data: dict,
    ) -> ElementVariablePaie:
        for field, value in data.items():
            setattr(element, field, value)
        element.save()
        return element

    def delete(self, element: ElementVariablePaie) -> None:
        element.delete()