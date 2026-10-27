from django.db.models import QuerySet
from django.core.files.base import ContentFile
from django.utils import timezone

from core.interfaces.ordre_virement_repository import OrdreVirementRepositoryInterface
from core.models import Employe, OrdreVirement, Paie
from core.models.enums import StatutPaie, StatutVirement


class OrdreVirementRepository(OrdreVirementRepositoryInterface):
    def all(self) -> QuerySet:
        return OrdreVirement.objects.select_related("employe", "decideur").defer("document_donnees").all()

    def get(self, ordre_virement_id: int) -> OrdreVirement:
        return OrdreVirement.objects.select_related("employe", "decideur").defer("document_donnees").get(pk=ordre_virement_id)

    def payroll_for_document(self, order: OrdreVirement, lock: bool = False) -> Paie:
        payrolls = Paie.objects.filter(
            employe_id=order.employe_id, periode=order.periode,
            statut=StatutPaie.VALIDEE, ordre_virement__isnull=True,
        )
        if lock:
            payrolls = payrolls.select_for_update()
        return payrolls.first()

    def save_document(self, order: OrdreVirement, snapshot: str, content: bytes, actor_id: int) -> OrdreVirement:
        order.document_donnees = snapshot
        order.document_genere_le = timezone.now()
        order.document_genere_par_id = actor_id
        order.document_pdf.save(f"ordre-virement-{order.pk}.pdf", ContentFile(content), save=False)
        try:
            order.save(update_fields=["document_donnees", "document_pdf", "document_genere_le", "document_genere_par"])
        except Exception:
            order.document_pdf.delete(save=False)
            raise
        return order

    def get_for_update(self, ordre_virement_id: int) -> OrdreVirement:
        return OrdreVirement.objects.select_related("employe").select_for_update(of=("self",)).get(pk=ordre_virement_id)

    def lock_employee(self, employee_id: int) -> None:
        Employe.objects.select_for_update().get(pk=employee_id)

    def has_active_order(self, employee_id: int, period: str, exclude_id: int = None) -> bool:
        orders = OrdreVirement.objects.filter(
            employe_id=employee_id, periode=period, statut__in=[StatutVirement.GENERE, StatutVirement.TRAITE],
        )
        if exclude_id is not None:
            orders = orders.exclude(pk=exclude_id)
        return orders.exists()

    def has_validated_payroll(self, employee_id: int, period: str) -> bool:
        return Paie.objects.filter(
            employe_id=employee_id, periode=period, statut=StatutPaie.VALIDEE, ordre_virement__isnull=True,
        ).exists()

    def create(self, data: dict) -> OrdreVirement:
        return OrdreVirement.objects.create(**data)

    def update(self, ordre_virement: OrdreVirement, data: dict) -> OrdreVirement:
        for field, value in data.items():
            setattr(ordre_virement, field, value)
        ordre_virement.save()
        return ordre_virement

    def delete(self, ordre_virement: OrdreVirement) -> None:
        ordre_virement.delete()

    def has_paid_payroll(self, ordre_virement_id: int) -> bool:
        return OrdreVirement.objects.filter(
            pk=ordre_virement_id,
            paiements__statut=StatutPaie.PAYE,
        ).exists()
