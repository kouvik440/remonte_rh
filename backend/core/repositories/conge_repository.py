from django.db.models import QuerySet
from django.db import transaction
from django.db.models.deletion import ProtectedError

from core.interfaces.conge_repository import LeaveTypeInUseError, TypeCongeRepositoryInterface
from core.models import TypeConge


class TypeCongeRepository(TypeCongeRepositoryInterface):
    def all(self) -> QuerySet:
        return TypeConge.objects.all()

    def get(self, type_conge_id: int) -> TypeConge:
        return TypeConge.objects.get(pk=type_conge_id)

    def create(self, data: dict) -> TypeConge:
        type_conge = TypeConge.objects.create(**data)
        return self.get(type_conge.pk)

    @transaction.atomic
    def update(self, type_conge: TypeConge, data: dict) -> TypeConge:
        for field, value in data.items():
            setattr(type_conge, field, value)
        type_conge.save()
        if "jours_par_annee" in data:
            type_conge.soldes.update(acquis=type_conge.jours_par_annee)
        return self.get(type_conge.pk)

    def delete(self, type_conge: TypeConge) -> None:
        if type_conge.soldes.exists():
            raise LeaveTypeInUseError
        try:
            type_conge.delete()
        except ProtectedError as error:
            raise LeaveTypeInUseError from error


