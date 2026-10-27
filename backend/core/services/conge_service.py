from django.db.models import QuerySet
from uuid import uuid4

from core.interfaces.conge_repository import LeaveTypeInUseError, TypeCongeRepositoryInterface
from rest_framework.exceptions import ValidationError
from core.models import TypeConge
from core.repositories.conge_repository import TypeCongeRepository


class CongeService:
    def __init__(
        self,
        type_conge_repository: TypeCongeRepositoryInterface,
    ):
        self.type_conge_repository = type_conge_repository

    # ---- Types de conge ----
    def get_all_types(self) -> QuerySet:
        return self.type_conge_repository.all()

    def get_type(self, type_conge_id: int) -> TypeConge:
        return self.type_conge_repository.get(type_conge_id)

    def create_type(self, data: dict) -> TypeConge:
        type_data = {**data, "code": f"CONGE_{uuid4().hex[:14].upper()}"}
        return self.type_conge_repository.create(type_data)

    def update_type(self, type_conge_id: int, data: dict) -> TypeConge:
        type_conge = self.type_conge_repository.get(type_conge_id)
        type_data = {key: value for key, value in data.items() if key != "code"}
        return self.type_conge_repository.update(type_conge, type_data)

    def delete_type(self, type_conge_id: int) -> None:
        type_conge = self.type_conge_repository.get(type_conge_id)
        try:
            self.type_conge_repository.delete(type_conge)
        except LeaveTypeInUseError as error:
            raise ValidationError({
                "detail": "Ce type possède des demandes ou des soldes. Désactivez-le plutôt que de le supprimer."
            }) from error


conge_service = CongeService(TypeCongeRepository())
