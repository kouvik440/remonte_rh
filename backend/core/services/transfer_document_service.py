import json
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.interfaces.coordonnees_bancaires_repository import CoordonneesBancairesRepositoryInterface
from core.interfaces.ordre_virement_repository import OrdreVirementRepositoryInterface
from core.models import CoordonneesBancaires
from core.models.enums import StatutPaie, StatutVirement
from core.repositories.coordonnees_bancaires_repository import CoordonneesBancairesRepository
from core.repositories.ordre_virement_repository import OrdreVirementRepository
from core.services.bank_rib import normalize_uemoa_rib
from core.services.transfer_order_pdf_service import TransferOrderPdfService


class TransferDocumentService:
    def __init__(self, orders: OrdreVirementRepositoryInterface, banks: CoordonneesBancairesRepositoryInterface, renderer):
        self.orders = orders
        self.banks = banks
        self.renderer = renderer

    def context(self, order_id):
        order = self.orders.get(order_id)
        self._check_order(order)
        payroll = self.orders.payroll_for_document(order)
        self._check_payroll(payroll)
        return {"ordre": order.pk, "periode": order.periode, "montant": str(payroll.salaire_net), "devise": "XOF",
                "beneficiaire": f"{order.employe.prenom} {order.employe.nom}".strip(),
                "comptes": [self._account_choice(account) for account in self.banks.for_employee(order.employe_id)]}

    @transaction.atomic
    def generate(self, order_id, data, actor_id):
        initial = self.orders.get(order_id)
        if initial.document_pdf:
            return initial
        self._check_order(initial)
        # Match the payment workflow's lock order: payroll first, transfer order second.
        payroll = self.orders.payroll_for_document(initial, lock=True)
        self._check_payroll(payroll)
        order = self.orders.get_for_update(order_id)
        if order.document_pdf:
            return order
        self._check_order(order)
        if order.employe_id != payroll.employe_id or order.periode != payroll.periode:
            raise ValidationError({"ordre": "L’ordre a changé pendant la préparation. Recommencez."})
        account = self._beneficiary_account(data["coordonnees_bancaires"], order.employe_id)
        snapshot = self._snapshot(order, payroll, account, data)
        content = self.renderer.render(snapshot)
        return self.orders.save_document(order, json.dumps(snapshot, ensure_ascii=False), content, actor_id)

    @staticmethod
    def _check_order(order):
        if order.statut != StatutVirement.GENERE:
            raise ValidationError({"statut": "Le document peut être préparé uniquement pour un ordre au statut Généré."})

    @staticmethod
    def _check_payroll(payroll):
        if payroll is None or payroll.statut != StatutPaie.VALIDEE:
            raise ValidationError({"paie": "Une paie validée correspondante est requise."})
        if payroll.devise != "XOF" or payroll.salaire_net is None or payroll.salaire_net <= Decimal("0"):
            raise ValidationError({"paie": "Le montant net validé doit être positif et libellé en XOF."})

    def _beneficiary_account(self, account_id, employee_id):
        try:
            account = self.banks.get(account_id)
        except CoordonneesBancaires.DoesNotExist as error:
            raise ValidationError({"coordonnees_bancaires": "Compte bénéficiaire introuvable."}) from error
        if account.employe_id != employee_id:
            raise ValidationError({"coordonnees_bancaires": "Le compte doit appartenir à l’employé de cet ordre."})
        try:
            normalize_uemoa_rib(account.iban)
        except ValueError as error:
            raise ValidationError({"coordonnees_bancaires": "Renseignez le RIB UEMOA complet du salarié dans ses coordonnées bancaires (24 caractères)."}) from error
        return account

    @staticmethod
    def _account_choice(account):
        try:
            normalize_uemoa_rib(account.iban)
            valid = True
        except ValueError:
            valid = False
        return {"id": account.pk, "banque": account.banque, "compte_masque": "•••• " + account.iban[-4:], "rib_valide": valid}

    @staticmethod
    def _snapshot(order, payroll, account, data):
        return {**{key: str(value) for key, value in data.items() if key != "coordonnees_bancaires"},
                "reference": f"OV-BF-{timezone.localdate().year}-{order.pk:06d}", "ordre_id": order.pk,
                "paie_id": payroll.pk, "periode": order.periode, "montant": str(payroll.salaire_net), "devise": "XOF",
                "beneficiaire_nom": f"{order.employe.prenom} {order.employe.nom}".strip(),
                "beneficiaire_adresse": order.employe.adresse, "beneficiaire_banque": account.banque,
                "beneficiaire_rib": normalize_uemoa_rib(account.iban), "compte_beneficiaire_id": account.pk,
                "date_emission": timezone.localdate().isoformat()}


transfer_document_service = TransferDocumentService(OrdreVirementRepository(), CoordonneesBancairesRepository(), TransferOrderPdfService())
