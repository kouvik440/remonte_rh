from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Employe, Poste, Contrat, EmployeHistorique, Role
from core.permission_codes import get_permission_by_code
from core.services.contrat_service import contrat_service


class PositionCatalogueTests(APITestCase):
    def setUp(self):
        self.hr = self.employee("hr")
        self.worker = self.employee("worker")
        self.other = self.employee("other")
        self.hr.roles.add(Role.objects.get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES"))
        self.client.force_authenticate(self.hr)

    @staticmethod
    def employee(name):
        return Employe.objects.create_user(email=f"position-{name}@example.com", matricule=f"POSITION-{name}",
            nom="Test", prenom=name, num_secu_sociale=f"POSITION-SSN-{name}", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="000")

    def create_position(self, name="Développeur"):
        response = self.client.post(reverse("poste-list"), {"nom": name, "description": "Poste du catalogue"}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def create_contract(self, employee, position):
        response = self.client.post(reverse("contrat-list"), {"employe": employee.pk, "date_debut": "2020-01-01",
            "salaire_base": "220000", "heures_journalieres": "8", "poste": position}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def test_catalogue_crud_and_case_insensitive_uniqueness(self):
        position = self.create_position("  Comptable  ")
        self.assertEqual(position["nom"], "Comptable")
        self.assertNotIn("employe", position)
        duplicate = self.client.post(reverse("poste-list"), {"nom": "comptable"}, format="json")
        self.assertEqual(duplicate.status_code, 400)
        endpoint = reverse("poste-detail", args=[position["id"]])
        updated = self.client.put(endpoint, {"nom": "Comptable principal", "description": "Comptabilité"}, format="json")
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(self.client.get(endpoint).data["description"], "Comptabilité")
        self.assertEqual(self.client.delete(endpoint).status_code, 204)

    def test_same_position_serves_multiple_contracts_and_is_protected_from_deletion(self):
        position = self.create_position()
        for employee in (self.worker, self.other):
            contract = self.create_contract(employee, position["id"])
            self.assertEqual(contract["poste_nom"], "Développeur")
            directory = self.client.get(reverse("employe-detail", args=[employee.pk]))
            self.assertEqual(directory.data["postes_actuels"], [{"id": position["id"], "nom": "Développeur"}])
        deleted = self.client.delete(reverse("poste-detail", args=[position["id"]]))
        self.assertEqual(deleted.status_code, 400)
        self.assertIn("utilisé", str(deleted.data))
        self.assertEqual(Contrat.objects.filter(poste_id=position["id"]).count(), 2)

    def test_changing_contract_position_preserves_old_and_new_position_history(self):
        first = self.create_position()
        second = self.create_position("Chef de projet")
        contract = self.create_contract(self.worker, first["id"])
        response = self.client.put(reverse("contrat-detail", args=[contract["id"]]), {
            "employe": self.worker.pk, "date_debut": "2020-01-01", "salaire_base": "220000", "heures_journalieres": "8", "poste": second["id"]}, format="json")
        self.assertEqual(response.status_code, 200)
        history = EmployeHistorique.objects.filter(employe=self.worker, categorie="POSTE").first()
        self.assertEqual(history.avant["nom"], "Développeur")
        self.assertEqual(history.apres["nom"], "Chef de projet")
        contract_history = EmployeHistorique.objects.filter(employe=self.worker, categorie="CONTRAT").first()
        self.assertEqual(contract_history.avant["poste"]["nom"], "Développeur")
        self.assertEqual(contract_history.apres["poste"]["nom"], "Chef de projet")
        self.assertEqual(contract_history.auteur_id, self.hr.pk)

    def test_catalogue_rename_keeps_assignment_and_old_history(self):
        position = self.create_position()
        contract = self.create_contract(self.worker, position["id"])
        Contrat.objects.create(employe=self.worker, poste_id=position["id"], date_debut="2019-01-01", date_fin="2019-12-31", salaire_base="180000", heures_journalieres="8", statut="CLOS")
        first_snapshot = EmployeHistorique.objects.filter(employe=self.worker, categorie="CONTRAT").first().apres
        response = self.client.put(reverse("poste-detail", args=[position["id"]]), {"nom": "Développeur confirmé"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.client.get(reverse("contrat-detail", args=[contract["id"]])).data["poste_nom"], "Développeur confirmé")
        self.assertEqual(first_snapshot["poste"]["nom"], "Développeur")
        history = EmployeHistorique.objects.filter(employe=self.worker, categorie="POSTE").first()
        self.assertEqual(history.avant["nom"], "Développeur")
        self.assertEqual(history.apres["nom"], "Développeur confirmé")
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker, categorie="POSTE").count(), 2)

    def test_catalogue_access_does_not_leak_into_simple_employee_role(self):
        position = self.create_position()
        self.worker.roles.add(Role.objects.get(nom="EMPLOYE_SIMPLE"))
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.get(reverse("poste-list")).status_code, 403)
        self.assertEqual(self.client.delete(reverse("poste-detail", args=[position["id"]])).status_code, 403)
        role = Role.objects.create(nom="POSITION_READ_ONLY")
        role.permissions.add(get_permission_by_code("poste.read"))
        self.worker.roles.add(role)
        self.assertEqual(self.client.get(reverse("poste-list")).status_code, 200)
        self.assertEqual(self.client.post(reverse("poste-list"), {"nom": "Interdit"}, format="json").status_code, 403)

    def test_unknown_position_is_rejected_and_old_contract_without_position_is_preserved(self):
        contract = Contrat.objects.create(employe=self.worker, date_debut="2020-01-01", salaire_base="220000", heures_journalieres="8")
        response = self.client.put(reverse("contrat-detail", args=[contract.pk]), {"employe": self.worker.pk, "date_debut": "2020-01-01",
            "salaire_base": "220000", "heures_journalieres": "8", "poste": 9999999}, format="json")
        self.assertEqual(response.status_code, 400)
        contract.refresh_from_db()
        self.assertIsNone(contract.poste_id)
