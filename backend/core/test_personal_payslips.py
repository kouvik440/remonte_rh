from django.core.files.base import ContentFile
from django.urls import reverse
from unittest.mock import patch
from rest_framework.test import APITestCase

from core.models import Employe, Paie, Role


class PersonalPayslipTests(APITestCase):
    def setUp(self):
        self.employee = self.user("awa")
        self.other = self.user("moussa")
        self.employee.roles.add(Role.objects.get(nom="EMPLOYE_SIMPLE"))
        self.client.force_authenticate(self.employee)
        self.url = reverse("personal-payslip-list")

    def user(self, name):
        return Employe.objects.create_user(email=f"payslip-{name}@example.com", matricule=f"SLIP-{name}",
            nom="Test", prenom=name, num_secu_sociale=f"SLIP-SSN-{name}", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="000")

    def payroll(self, employee, month="10", status="VALIDEE"):
        return Paie.objects.create(employe=employee, periode=f"2026-{month}", libelle="Salaire mensuel", statut=status,
            salaire_brut="300000", salaire_net="250000")

    def test_personal_list_only_contains_own_finalized_payrolls_newest_first(self):
        older = self.payroll(self.employee, "09")
        newer = self.payroll(self.employee, "10", "PAYE")
        self.payroll(self.other)
        for month, status in (("06", "BROUILLON"), ("07", "CALCULE"), ("08", "ANNULE")):
            self.payroll(self.employee, month, status)
        response = self.client.get(self.url, {"employe": self.other.pk})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([row["id"] for row in response.data], [newer.pk, older.pk])
        self.assertEqual(response["Cache-Control"], "private, no-store")
        for row in response.data:
            self.assertNotIn("detail_calcul", row)
            self.assertNotIn("bulletin_pdf", row)
            self.assertEqual(row["salaire_net"], "250000.00")

    def test_legacy_payroll_without_pdf_remains_visible_with_unavailable_flag(self):
        self.payroll(self.employee)
        response = self.client.get(self.url)
        self.assertFalse(response.data[0]["bulletin_disponible"])

    def test_personal_endpoint_does_not_grant_global_payroll_access_or_generation(self):
        payroll = self.payroll(self.employee)
        self.assertEqual(self.client.get(reverse("paie-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("paie-detail", args=[payroll.pk])).status_code, 403)
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, 405)
        self.assertEqual(self.client.post(reverse("paie-bulletin", args=[payroll.pk]), {}, format="json").status_code, 403)

    def test_owner_can_download_archived_pdf_but_another_employee_cannot(self):
        payroll = self.payroll(self.employee)
        pdf = b"%PDF-1.4\nPersonal test document\n%%EOF"
        payroll.bulletin_pdf.save("personal-test.pdf", ContentFile(pdf))
        self.assertTrue(self.client.get(self.url).data[0]["bulletin_disponible"])
        endpoint = reverse("paie-bulletin", args=[payroll.pk])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(endpoint).status_code, 403)
        self.assertEqual(self.client.get(self.url).data, [])
        self.client.force_authenticate(self.employee)
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(b"".join(response.streaming_content), pdf)
        with patch("django.core.signals.request_finished.send"):
            response.close()

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_even_payroll_manager_personal_list_stays_personal(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS"))
        own = self.payroll(self.employee)
        self.payroll(self.other)
        self.assertEqual([row["id"] for row in self.client.get(self.url).data], [own.pk])
