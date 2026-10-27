from django.db.models import QuerySet
from django.db import transaction
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError
from rest_framework.exceptions import ValidationError
from .employe_history_service import record_change, position_snapshot

from core.interfaces.poste_repository import PosteRepositoryInterface
from core.models import Poste
from core.repositories.poste_repository import PosteRepository


class PosteService:
    def __init__(self, repository: PosteRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, poste_id: int) -> Poste:
        return self.repository.get(poste_id)

    @transaction.atomic
    def create(self, data: dict, actor=None) -> Poste:
        try:
            return self.repository.create(data)
        except IntegrityError as error:
            raise ValidationError({"nom": "Un poste portant ce nom existe déjà."}) from error

    @transaction.atomic
    def update(self, poste_id: int, data: dict, actor=None) -> Poste:
        poste = Poste.objects.select_for_update().get(pk=poste_id)
        before = position_snapshot(poste)
        try:
            updated = self.repository.update(poste, data)
        except IntegrityError as error:
            raise ValidationError({"nom": "Un poste portant ce nom existe déjà."}) from error
        for employee_id in updated.contrats.order_by().values_list("employe_id", flat=True).distinct():
            record_change(employee_id, "POSTE", poste.pk, before, position_snapshot(updated), actor)
        return updated

    @transaction.atomic
    def delete(self, poste_id: int, actor=None) -> None:
        poste = Poste.objects.select_for_update().get(pk=poste_id)
        try:
            self.repository.delete(poste)
        except ProtectedError as error:
            raise ValidationError({"detail": "Ce poste est utilisé par un contrat et ne peut pas être supprimé."}) from error


poste_service = PosteService(PosteRepository())
