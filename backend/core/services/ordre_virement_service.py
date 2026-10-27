from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.interfaces.ordre_virement_repository import OrdreVirementRepositoryInterface
from core.models import OrdreVirement
from core.models.enums import StatutVirement
from core.repositories.ordre_virement_repository import OrdreVirementRepository


class OrdreVirementService:
    def __init__(self, repository: OrdreVirementRepositoryInterface):
        self.repository = repository

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def get(self, ordre_virement_id: int) -> OrdreVirement:
        return self.repository.get(ordre_virement_id)

    def get_locked(self, ordre_virement_id: int) -> OrdreVirement:
        return self.repository.get_for_update(ordre_virement_id)

    @transaction.atomic
    def create(self, data: dict) -> OrdreVirement:
        self._ensure_available(data["employe"].pk, data["periode"])
        data["statut"] = StatutVirement.GENERE
        data["date_traitement"] = None
        return self.repository.create(data)

    @transaction.atomic
    def update(self, ordre_virement_id: int, data: dict) -> OrdreVirement:
        ordre_virement = self.repository.get_for_update(ordre_virement_id)
        if ordre_virement.statut != StatutVirement.GENERE:
            raise ValidationError({"statut": "Seul un ordre généré peut être modifié."})
        if ordre_virement.document_pdf:
            raise ValidationError({"document": "Cet ordre possède un document figé. Annulez-le pour préparer un remplacement."})
        employee_id = data["employe"].pk if "employe" in data else ordre_virement.employe_id
        self._ensure_available(employee_id, data.get("periode", ordre_virement.periode), ordre_virement.pk)
        return self.repository.update(ordre_virement, data)

    def traiter(self, ordre_virement_id: int, motif: str = "", decideur_id: int = None) -> OrdreVirement:
        return self._decide(ordre_virement_id, StatutVirement.TRAITE, motif, decideur_id)

    def rejeter(self, ordre_virement_id: int, motif: str = "", decideur_id: int = None) -> OrdreVirement:
        return self._decide(ordre_virement_id, StatutVirement.REJETE, motif, decideur_id)

    def annuler(self, ordre_virement_id: int, motif: str = "", decideur_id: int = None) -> OrdreVirement:
        return self._decide(ordre_virement_id, StatutVirement.ANNULE, motif, decideur_id)

    @transaction.atomic
    def _decide(self, ordre_virement_id, target_status, motif, decideur_id):
        ordre = self.repository.get_for_update(ordre_virement_id)
        if ordre.statut != StatutVirement.GENERE:
            raise ValidationError({"statut": "Seul un ordre généré peut recevoir une décision."})
        if target_status in (StatutVirement.REJETE, StatutVirement.ANNULE) and not motif.strip():
            raise ValidationError({"motif": "Un motif est obligatoire pour cette décision."})
        now = timezone.now()
        changes = {"statut": target_status, "date_decision": now, "decideur_id": decideur_id, "motif_decision": motif.strip()}
        if target_status == StatutVirement.TRAITE:
            changes["date_traitement"] = now
        return self.repository.update(ordre, changes)

    @transaction.atomic
    def delete(self, ordre_virement_id: int) -> None:
        ordre_virement = self.repository.get_for_update(ordre_virement_id)
        if ordre_virement.statut != StatutVirement.GENERE:
            raise ValidationError({"statut": "Seul un ordre généré peut être supprimé."})
        if ordre_virement.document_pdf:
            raise ValidationError({"document": "Un ordre documenté doit être conservé. Utilisez l’annulation avec motif."})
        if self.repository.has_paid_payroll(ordre_virement_id):
            raise ValidationError({"ordre_virement": "Cet ordre est lié à une paie payée."})
        self.repository.delete(ordre_virement)

    def _ensure_available(self, employee_id, period, exclude_id=None):
        self.repository.lock_employee(employee_id)
        if self.repository.has_active_order(employee_id, period, exclude_id):
            raise ValidationError({"periode": "Un ordre généré ou traité existe déjà pour cet employé et cette période."})
        if not self.repository.has_validated_payroll(employee_id, period):
            raise ValidationError({"periode": "Une paie validée sans ordre associé est requise pour cet employé et cette période."})


ordre_virement_service = OrdreVirementService(OrdreVirementRepository())
