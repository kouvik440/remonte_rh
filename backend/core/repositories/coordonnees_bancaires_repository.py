from django.db.models import QuerySet
from django.db import IntegrityError, transaction

from core.interfaces.coordonnees_bancaires_repository import BankIbanAlreadyUsedError, CoordonneesBancairesRepositoryInterface
from core.security import iban_fingerprint
from core.models import CoordonneesBancaires


class CoordonneesBancairesRepository(CoordonneesBancairesRepositoryInterface):
    def iban_exists(self, fingerprint: str, exclude_id: int = None) -> bool:
        records = CoordonneesBancaires.objects.filter(iban_fingerprint=fingerprint)
        if exclude_id is not None:
            records = records.exclude(pk=exclude_id)
        return records.exists()

    def all(self) -> QuerySet:
        return CoordonneesBancaires.objects.select_related("employe").all()

    def for_employee(self, employee_id: int) -> QuerySet:
        return self.all().filter(employe_id=employee_id)

    def get(self, coordonnees_bancaires_id: int) -> CoordonneesBancaires:
        return self.all().get(pk=coordonnees_bancaires_id)

    def create(self, data: dict) -> CoordonneesBancaires:
        return self._save(CoordonneesBancaires(**data))

    def update(self, coordonnees_bancaires: CoordonneesBancaires, data: dict) -> CoordonneesBancaires:
        for field, value in data.items():
            setattr(coordonnees_bancaires, field, value)
        return self._save(coordonnees_bancaires)

    def _save(self, details: CoordonneesBancaires) -> CoordonneesBancaires:
        try:
            with transaction.atomic():
                details.save()
        except IntegrityError as error:
            if self.iban_exists(iban_fingerprint(details.iban), exclude_id=details.pk):
                raise BankIbanAlreadyUsedError from error
            raise
        return details

    def delete(self, coordonnees_bancaires: CoordonneesBancaires) -> None:
        coordonnees_bancaires.delete()
