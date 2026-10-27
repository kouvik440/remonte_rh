from django.db.models import QuerySet
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.interfaces.paie_repository import PaieRepositoryInterface
from core.models import OrdreVirement, Paie
from core.models.enums import StatutPaie, StatutVirement
from core.repositories.paie_repository import PaieRepository
from core.services.bulletin_paie_pdf_service import BulletinPaiePdfService
from core.services.ordre_virement_service import ordre_virement_service


class PaieService:
    def __init__(
        self,
        repository: PaieRepositoryInterface,
        ordre_virement_service,
        bulletin_pdf_service,
    ):
        self.repository = repository
        self.ordre_virement_service = ordre_virement_service
        self.bulletin_pdf_service = bulletin_pdf_service

    def get_all(self) -> QuerySet:
        return self.repository.all()

    def for_employee(self, employee_id: int) -> QuerySet:
        return self.repository.for_employee(employee_id)

    def get(self, paie_id: int) -> Paie:
        return self.repository.get(paie_id)

    @transaction.atomic
    def generate_bulletin(self, paie_id: int) -> Paie:
        paie = self.repository.get_for_update(paie_id)
        if paie.bulletin_pdf:
            return paie
        if paie.statut not in (StatutPaie.VALIDEE, StatutPaie.PAYE):
            raise ValidationError(
                {"statut": "Le bulletin est disponible après validation de la paie."}
            )
        content = self.bulletin_pdf_service.render(paie)
        filename = f"bulletin-paie-{paie.periode}-{paie.pk}.pdf"
        try:
            return self.repository.save_bulletin(paie, filename, content)
        except OSError as error:
            raise ValidationError({"bulletin": "Impossible d'archiver le bulletin PDF. Opération annulée ; réessayez après vérification du stockage."}) from error

    def create(self, data: dict) -> Paie:
        if data.get("ordre_virement") is not None:
            raise ValidationError(
                {"ordre_virement": "La paie doit être calculée et validée avant le virement."}
            )
        if self.repository.exists_for_employee_period(
            data["employe"].pk,
            data["periode"],
        ):
            raise ValidationError(
                {"periode": "Une paie existe déjà pour cet employé et cette période."}
            )
        return self.repository.create(data)

    def update(self, paie_id: int, data: dict) -> Paie:
        paie = self.repository.get(paie_id)
        if paie.statut != StatutPaie.BROUILLON:
            raise ValidationError(
                {"statut": "Seule une paie en brouillon peut être modifiée."}
            )
        if data.get("ordre_virement") is not None:
            raise ValidationError(
                {"ordre_virement": "Associez le virement après validation de la paie."}
            )
        employe = data.get("employe", paie.employe)
        periode = data.get("periode", paie.periode)
        if self.repository.exists_for_employee_period(
            employe.pk,
            periode,
            exclude_paie_id=paie.pk,
        ):
            raise ValidationError(
                {"periode": "Une paie existe déjà pour cet employé et cette période."}
            )
        return self.repository.update(paie, data)

    def delete(self, paie_id: int) -> None:
        paie = self.repository.get(paie_id)
        if paie.statut != StatutPaie.BROUILLON:
            raise ValidationError(
                {"statut": "Seule une paie en brouillon peut être supprimée."}
            )
        self.repository.delete(paie)

    @transaction.atomic
    def valider(self, paie_id: int, valideur_id: int) -> Paie:
        paie = self.repository.get_for_update(paie_id)
        if paie.statut != StatutPaie.CALCULE:
            raise ValidationError(
                {"statut": "Seule une paie calculée peut être validée."}
            )
        paie.statut = StatutPaie.VALIDEE
        paie.valideur_id = valideur_id
        paie.date_validation = timezone.now()
        self.repository.update(
            paie,
            {
                "statut": paie.statut,
                "valideur_id": paie.valideur_id,
                "date_validation": paie.date_validation,
            },
        )
        return self.generate_bulletin(paie_id)

    def annuler(self, paie_id: int, annule_par_id: int, motif: str) -> Paie:
        paie = self.repository.get(paie_id)
        if paie.statut not in (
            StatutPaie.BROUILLON,
            StatutPaie.CALCULE,
            StatutPaie.VALIDEE,
        ):
            raise ValidationError(
                {"statut": "Seule une paie non payée peut être annulée."}
            )
        if not motif.strip():
            raise ValidationError({"motif": "Le motif d'annulation est obligatoire."})
        paie.statut = StatutPaie.ANNULE
        paie.annule_par_id = annule_par_id
        paie.date_annulation = timezone.now()
        paie.motif_annulation = motif.strip()
        return self.repository.update(
            paie,
            {
                "statut": paie.statut,
                "annule_par_id": paie.annule_par_id,
                "date_annulation": paie.date_annulation,
                "motif_annulation": paie.motif_annulation,
            },
        )

    @transaction.atomic
    def marquer_payee(self, paie_id: int, ordre_virement_id: int) -> Paie:
        paie = self.repository.get_for_update(paie_id)
        if paie.statut != StatutPaie.VALIDEE:
            raise ValidationError(
                {"statut": "Seule une paie validée peut être marquée payée."}
            )
        try:
            ordre = self.ordre_virement_service.get_locked(ordre_virement_id)
        except OrdreVirement.DoesNotExist as error:
            raise ValidationError(
                {"ordre_virement": "Ordre de virement non trouvé."}
            ) from error
        if ordre.employe_id != paie.employe_id or ordre.periode != paie.periode:
            raise ValidationError(
                {"ordre_virement": "L'ordre doit concerner le même employé et la même période."}
            )
        if ordre.statut != StatutVirement.TRAITE or ordre.date_traitement is None:
            raise ValidationError(
                {"ordre_virement": "L'ordre doit être traité et daté avant de marquer la paie payée."}
            )
        if self.repository.order_used_by_other_payroll(ordre.pk, paie.pk):
            raise ValidationError(
                {"ordre_virement": "Cet ordre est déjà associé à une autre paie."}
            )
        paie.ordre_virement = ordre
        paie.statut = StatutPaie.PAYE
        paie.date_paiement = ordre.date_traitement
        return self.repository.update(
            paie,
            {
                "ordre_virement": ordre,
                "statut": paie.statut,
                "date_paiement": paie.date_paiement,
            },
        )


paie_service = PaieService(
    PaieRepository(),
    ordre_virement_service,
    BulletinPaiePdfService(),
)
