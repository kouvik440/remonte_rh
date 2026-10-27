from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Employe, Role
from core.permission_codes import permission_code


class PayrollMassRoleTests(TestCase):
    def test_module_profile_is_read_only_and_not_assigned_to_employees(self):
        role = Role.objects.get(nom="FRONTEND_MODULE_5_MASSE_SALARIALE")
        codes = {permission_code(item) for item in role.permissions.select_related("content_type")}
        self.assertEqual(codes, {"paie.read", "departement.read"})
        self.assertFalse(Employe.objects.filter(roles=role).exists())


class PayrollMassProfileApiTests(APITestCase):
    def setUp(self):
        self.employee = Employe.objects.create_user(
            email="payroll-mass@example.com", password="test-only-password",
            nom="Test", prenom="Analyse", matricule="MASS-001",
            num_secu_sociale="MASS-SSN-001", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )
        self.client.force_authenticate(self.employee)
        self.query = {"periode_debut": "2026-01", "periode_fin": "2026-12"}

    def test_profile_can_read_analyses_and_export_but_cannot_create_payroll(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_5_MASSE_SALARIALE"))
        for route in ("masse-salariale", "masse-salariale-evolution", "departement-list"):
            self.assertEqual(self.client.get(reverse(route), self.query).status_code, 200)
        for format_name, signature in (("csv", b"\xef\xbb\xbf"), ("xlsx", b"PK"), ("pdf", b"%PDF")):
            response = self.client.get(reverse("masse-salariale-export"), {**self.query, "format_fichier": format_name})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(signature))
        self.assertEqual(self.client.post(reverse("paie-list"), {}, format="json").status_code, 403)

    def test_employee_without_permission_cannot_read_or_export_analyses(self):
        for route in ("masse-salariale", "masse-salariale-evolution", "masse-salariale-export"):
            response = self.client.get(reverse(route), {**self.query, "format_fichier": "csv"})
            self.assertEqual(response.status_code, 403)
