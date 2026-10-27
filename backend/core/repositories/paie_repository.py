from django.core.files.base import ContentFile
import logging
from django.db.models import QuerySet

from core.interfaces.paie_repository import PaieRepositoryInterface
from core.models import Contrat, Employe, Paie
from core.models.enums import StatutPaie


class PaieRepository(PaieRepositoryInterface):
    def all(self) -> QuerySet:
        return Paie.objects.select_related("employe", "ordre_virement").all()

    def for_employee(self, employee_id: int) -> QuerySet:
        return Paie.objects.filter(employe_id=employee_id, statut__in=(StatutPaie.VALIDEE, StatutPaie.PAYE)).order_by("-periode", "-pk")

    def exists_for_employee_period(
        self,
        employee_id: int,
        periode: str,
        exclude_paie_id: int = None,
    ) -> bool:
        paies = Paie.objects.filter(employe_id=employee_id, periode=periode).exclude(
            statut=StatutPaie.ANNULE
        )
        if exclude_paie_id is not None:
            paies = paies.exclude(pk=exclude_paie_id)
        return paies.exists()

    def get(self, paie_id: int) -> Paie:
        return Paie.objects.select_related("employe", "ordre_virement").get(pk=paie_id)

    def get_for_update(self, paie_id: int) -> Paie:
        return Paie.objects.select_for_update().get(pk=paie_id)

    def create(self, data: dict) -> Paie:
        return Paie.objects.create(**data)

    def update(self, paie: Paie, data: dict) -> Paie:
        for field, value in data.items():
            setattr(paie, field, value)
        paie.save()
        return paie

    def save_bulletin(self, paie: Paie, filename: str, content: bytes) -> Paie:
        previous_name = paie.bulletin_pdf.name
        try:
            paie.bulletin_pdf.save(filename, ContentFile(content), save=True)
        except Exception:
            if paie.bulletin_pdf.name and paie.bulletin_pdf.name != previous_name:
                try:
                    paie.bulletin_pdf.storage.delete(paie.bulletin_pdf.name)
                except OSError:
                    logging.getLogger(__name__).exception("Échec du nettoyage du bulletin après erreur d'archivage (paie %s).", paie.pk)
            raise
        return paie

    def get_classification_snapshot(self, employee_id: int, contract_id: int) -> dict:
        employee = Employe.objects.select_related("department").get(pk=employee_id)
        contract = Contrat.objects.prefetch_related("type").get(pk=contract_id)
        department = employee.department
        return {
            "departement": (
                {"id": department.pk, "nom": department.nom}
                if department
                else None
            ),
            "types_contrat": [
                {"id": contract_type.pk, "type": contract_type.type}
                for contract_type in contract.type.all()
            ],
        }

    def order_used_by_other_payroll(self, ordre_virement_id: int, paie_id: int) -> bool:
        return Paie.objects.filter(ordre_virement_id=ordre_virement_id).exclude(
            pk=paie_id
        ).exists()

    def delete(self, paie: Paie) -> None:
        paie.delete()
