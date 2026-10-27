import json
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import CoordonneesBancaires, Employe, OrdreVirement, Paie, Role
from core.permission_codes import get_permission_by_code
from core.storage import PrivatePayrollStorage


class TransferDocumentTests(APITestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix="transfer-document-tests-")
        self.addCleanup(folder.cleanup)
        storage_patch = patch.object(OrdreVirement._meta.get_field("document_pdf"), "storage", PrivatePayrollStorage(location=folder.name))
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.employee = self.make_employee("ONE")
        self.other = self.make_employee("TWO")
        self.client.force_authenticate(self.employee)
        self.payroll = Paie.objects.create(employe=self.employee, periode="2026-10", libelle="Salaire", statut="VALIDEE", salaire_net=Decimal("325000.50"))
        self.order = OrdreVirement.objects.create(employe=self.employee, periode="2026-10", date_generation=timezone.now())
        self.bank = CoordonneesBancaires.objects.create(employe=self.employee, banque="Banque bénéficiaire", iban="BF0020100200000000000290")
        self.payload = {
            "coordonnees_bancaires": self.bank.pk, "donneur_nom": "Entreprise test", "donneur_adresse": "Adresse test à Ouagadougou",
            "donneur_telephone": "+226 00000000", "banque": "Banque entreprise", "agence": "Ouagadougou",
            "compte_debit": "BF0010100100000000000189", "lieu": "Ouagadougou",
            "date_execution": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "motif": "Salaire octobre", "signataire": "Direction financière", "fonction_signataire": "Directeur", "canal": "BANQUE",
        }

    def make_employee(self, suffix):
        return Employe.objects.create_user(email=f"transfer-document-{suffix}@example.com", password=None,
            nom="Test", prenom=suffix, matricule=f"PDF-{suffix}", num_secu_sociale=f"PDF-SSN-{suffix}",
            date_naissance="1990-01-01", date_entree="2020-01-01", adresse="Ouagadougou", telephone="0000")

    def grant(self, *codes):
        role = Role.objects.create(nom="TRANSFER-DOC-TEST")
        role.permissions.set([get_permission_by_code(code) for code in codes])
        self.employee.roles.add(role)

    def manager(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS"))

    def generate(self, **changes):
        return self.client.post(reverse("transfer-document", args=[self.order.pk]), {**self.payload, **changes}, format="json")

    def test_generation_creates_private_pdf_and_encrypted_snapshot_without_executing_payment(self):
        self.manager()
        generated = self.generate(montant="1", beneficiaire_nom="Wrong recipient")
        self.assertEqual(generated.status_code, 200, generated.data)
        self.order.refresh_from_db()
        snapshot = json.loads(self.order.document_donnees)
        self.assertEqual(snapshot["montant"], "325000.50")
        self.assertEqual(snapshot["beneficiaire_rib"], self.bank.iban)
        self.assertEqual(snapshot["beneficiaire_nom"], "ONE Test")
        self.assertEqual(self.order.document_genere_par_id, self.employee.pk)
        self.assertEqual(self.order.statut, "GENERE")
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.statut, "VALIDEE")
        self.assertIsNone(self.payroll.ordre_virement_id)
        with connection.cursor() as cursor:
            cursor.execute("SELECT document_donnees FROM core_ordrevirement WHERE id=%s", [self.order.pk])
            stored = cursor.fetchone()[0]
        self.assertNotIn(self.payload["compte_debit"], stored)
        self.assertNotIn(self.bank.iban, stored)
        self.assertNotEqual(stored, self.order.document_donnees)
        listing = self.client.get(reverse("ordre-virement-list"))
        self.assertNotIn("document_donnees", listing.data[0])
        self.assertNotIn("document_pdf", listing.data[0])
        downloaded = self.client.get(reverse("transfer-document", args=[self.order.pk]), HTTP_ACCEPT="*/*")
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded["Content-Type"], "application/pdf")
        self.assertEqual(downloaded["Cache-Control"], "private, no-store")
        self.assertTrue(b"".join(downloaded.streaming_content).startswith(b"%PDF"))

    def test_context_limits_bank_choices_to_recipient_and_masks_account_numbers(self):
        self.manager()
        other_bank = CoordonneesBancaires.objects.create(employe=self.other, banque="Other", iban="BF0030100300000000000391")
        response = self.client.get(reverse("transfer-document-context", args=[self.order.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data["comptes"]], [self.bank.pk])
        self.assertNotIn(self.bank.iban, json.dumps(response.data))
        self.assertNotIn(other_bank.pk, [row["id"] for row in response.data["comptes"]])

    def test_generation_and_download_require_export_right_in_addition_to_read_permissions(self):
        self.grant("ordre_virement.read", "paie.read", "ordre_virement.update")
        self.assertEqual(self.generate().status_code, 403)
        self.assertEqual(self.client.get(reverse("transfer-document-context", args=[self.order.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("transfer-document", args=[self.order.pk])).status_code, 403)

    def test_export_right_alone_cannot_expose_financial_data(self):
        self.grant("ordre_virement.generate_document")
        self.assertEqual(self.generate().status_code, 403)

    def test_recipient_account_and_rib_format_are_validated(self):
        self.manager()
        other_bank = CoordonneesBancaires.objects.create(employe=self.other, banque="Other", iban="BF0030100300000000000391")
        self.assertEqual(self.generate(coordonnees_bancaires=other_bank.pk).status_code, 400)
        self.assertEqual(self.generate(compte_debit="FR123").status_code, 400)
        self.assertEqual(self.generate(date_execution="2020-01-01").status_code, 400)
        self.bank.iban = "FR761234567890"
        self.bank.save()
        response = self.generate()
        self.assertEqual(response.status_code, 400)
        self.assertIn("coordonnees_bancaires", response.data)

    def test_paid_or_rejected_orders_and_invalid_payroll_cannot_produce_new_instructions(self):
        self.manager()
        for state in ("TRAITE", "REJETE", "ANNULE"):
            self.order.statut = state
            self.order.save()
            self.assertEqual(self.generate().status_code, 400)
        self.order.statut = "GENERE"
        self.order.save()
        self.payroll.salaire_net = 0
        self.payroll.save()
        self.assertEqual(self.generate().status_code, 400)
        self.payroll.statut = "CALCULE"
        self.payroll.save()
        self.assertEqual(self.generate().status_code, 400)

    def test_archived_document_is_idempotent_and_locks_editing_and_deletion(self):
        self.manager()
        self.assertEqual(self.generate().status_code, 200)
        self.order.refresh_from_db()
        path, snapshot = self.order.document_pdf.name, self.order.document_donnees
        self.assertEqual(self.generate(donneur_nom="Changed").status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.document_pdf.name, path)
        self.assertEqual(self.order.document_donnees, snapshot)
        url = reverse("ordre-virement-detail", args=[self.order.pk])
        self.assertEqual(self.client.put(url, {"employe": self.employee.pk, "periode": "2026-10"}, format="json").status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 400)
        canceled = self.client.post(reverse("ordre-virement-annuler", args=[self.order.pk]), {"motif": "Correction des instructions"}, format="json")
        self.assertEqual(canceled.status_code, 200)
