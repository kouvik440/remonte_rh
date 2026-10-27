from django.db.models import QuerySet

from core.interfaces.poste_repository import PosteRepositoryInterface
from core.models import Poste


class PosteRepository(PosteRepositoryInterface):
    def all(self) -> QuerySet:
        return Poste.objects.all()

    def get(self, poste_id: int) -> Poste:
        return Poste.objects.get(pk=poste_id)

    def create(self, data: dict) -> Poste:
        return Poste.objects.create(**data)

    def update(self, poste: Poste, data: dict) -> Poste:
        for field, value in data.items():
            setattr(poste, field, value)
        poste.save()
        return poste

    def delete(self, poste: Poste) -> None:
        poste.delete()
