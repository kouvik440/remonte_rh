from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Departement, Employe, Role


class DepartmentsApiTests(APITestCase):
    def setUp(self):
        self.employee = Employe.objects.create_user(
            email="department-test@example.com", password=None,
            matricule="DEP-TEST", num_secu_sociale="DEP-SSN-TEST",
            nom="Test", prenom="Département", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )
        self.client.force_authenticate(self.employee)
        self.list_url = reverse("departement-list")

    def manage(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES"))

    def test_module_one_can_create_read_update_and_delete_department(self):
        self.manage()
        created = self.client.post(self.list_url, {"nom": "Recherche"}, format="json")
        self.assertEqual(created.status_code, 201)
        url = reverse("departement-detail", args=[created.data["id"]])
        self.assertIn(created.data, self.client.get(self.list_url).data)
        self.assertEqual(self.client.get(url).data, created.data)
        updated = self.client.put(url, {"nom": "Recherche et développement"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["nom"], "Recherche et développement")
        self.assertEqual(updated.data["code"], created.data["code"])
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_read_only_module_five_cannot_create_update_or_delete(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_5_MASSE_SALARIALE"))
        department = Departement.objects.create(nom="Lecture", code="LECT")
        url = reverse("departement-detail", args=[department.pk])
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.post(self.list_url, {"nom": "Interdit", "code": "NON"}).status_code, 403)
        self.assertEqual(self.client.put(url, {"nom": "Interdit", "code": "NON"}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.assertTrue(Departement.objects.filter(pk=department.pk).exists())

    def test_employee_without_permission_cannot_read_departments(self):
        self.assertEqual(self.client.get(self.list_url).status_code, 403)

    def test_duplicate_and_blank_fields_are_rejected_without_changing_existing_department(self):
        self.manage()
        department = Departement.objects.create(nom="Finance", code="FIN")
        for payload, field in (({"nom": "Finance"}, "nom"),
                               ({"nom": " "}, "nom"),
                               ({"nom": "N" * 101}, "nom")):
            with self.subTest(payload=payload):
                response = self.client.post(self.list_url, payload, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data)
        department.refresh_from_db()
        self.assertEqual(department.nom, "Finance")

    def test_generated_codes_are_distinct_and_client_code_is_ignored(self):
        self.manage()
        first = self.client.post(self.list_url, {"nom": "Administration", "code": "MANUEL"}, format="json")
        second = self.client.post(self.list_url, {"nom": "Comptabilité"}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertTrue(first.data["code"])
        self.assertLessEqual(len(first.data["code"]), 20)
        self.assertNotEqual(first.data["code"], "MANUEL")
        self.assertNotEqual(first.data["code"], second.data["code"])

    def test_renaming_existing_department_preserves_its_legacy_code(self):
        self.manage()
        department = Departement.objects.create(nom="Administration", code="REC-ADM")
        response = self.client.put(reverse("departement-detail", args=[department.pk]),
                                   {"nom": "Administration générale", "code": "AUTRE"}, format="json")
        self.assertEqual(response.status_code, 200)
        department.refresh_from_db()
        self.assertEqual(department.nom, "Administration générale")
        self.assertEqual(department.code, "REC-ADM")

    def test_deleting_department_keeps_employee_and_removes_assignment(self):
        self.manage()
        department = Departement.objects.create(nom="Temporaire", code="TEMP")
        self.employee.department = department
        self.employee.save(update_fields=["department"])
        response = self.client.delete(reverse("departement-detail", args=[department.pk]))
        self.assertEqual(response.status_code, 204)
        self.employee.refresh_from_db()
        self.assertIsNone(self.employee.department_id)
