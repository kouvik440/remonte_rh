from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Employe, Poste, Contrat, TypeContrat, EmployeHistorique, Role
from core.permission_codes import get_permission_by_code
from core.services.employe_service import employe_service
from core.services.contrat_service import contrat_service


class EmployeeHierarchyHistoryTests(APITestCase):
    def setUp(self):
        self.hr = self.employee("hr")
        self.worker = self.employee("worker")
        self.manager = self.employee("manager")
        self.hr.roles.add(Role.objects.get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES"))
        self.client.force_authenticate(self.hr)

    @staticmethod
    def employee(name):
        return Employe.objects.create_user(email=f"hierarchy-{name}@example.com", matricule=f"H-{name}", nom="Test", prenom=name,
            date_naissance="1990-01-01", date_entree="2020-01-01", adresse="Test", telephone="000", num_secu_sociale=f"H-SSN-{name}")

    def payload(self, employee, **changes):
        return {"email": employee.email, "matricule": employee.matricule, "nom": employee.nom, "prenom": employee.prenom,
            "date_naissance": "1990-01-01", "date_entree": "2020-01-01", "adresse": "Test", "telephone": "000",
            "num_secu_sociale": employee.num_secu_sociale, **changes}

    def update(self, employee, **changes):
        return self.client.put(reverse("employe-detail", args=[employee.pk]), self.payload(employee, **changes), format="json")

    def test_hr_assigns_manager_and_position_and_history_has_author_and_values(self):
        first = Poste.objects.create(nom="Développeur")
        second = Poste.objects.create(nom="Chef de projet")
        contract = contrat_service.create({"employe": self.worker, "date_debut": "2020-01-01", "salaire_base": "200000.00", "heures_journalieres": "8", "poste": first}, actor=self.hr)
        response = self.update(self.worker, responsable=self.manager.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["responsable"], self.manager.pk)
        self.assertEqual(response.data["poste_nom"], "Développeur")
        contrat_service.update(contract.pk, {"poste": second}, actor=self.hr)
        changed = self.update(self.worker, responsable=None)
        self.assertEqual(changed.status_code, 200, changed.data)
        events = self.client.get(reverse("employee-history", args=[self.worker.pk]))
        self.assertEqual(len(events.data), 6)
        position = next(item for item in events.data if item["categorie"] == "POSTE")
        self.assertEqual(position["avant"]["nom"], "Développeur")
        self.assertEqual(position["apres"]["nom"], "Chef de projet")
        self.assertEqual(position["auteur_nom"], self.hr.get_full_name())
        self.assertEqual(events["Cache-Control"], "private, no-store")
        # Identical values do not add events; clearing the position records its removal.
        self.update(self.worker, responsable=None)
        contrat_service.update(contract.pk, {"poste": second}, actor=self.hr)
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker).count(), 6)
        contrat_service.update(contract.pk, {"poste": None}, actor=self.hr)
        self.assertTrue(Poste.objects.filter(pk=second.pk).exists())
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker, categorie="POSTE").first().operation, "SUPPRESSION")

    def test_self_management_indirect_cycle_and_inactive_manager_are_rejected_atomically(self):
        self.assertEqual(self.update(self.worker, responsable=self.worker.pk).status_code, 400)
        self.assertEqual(self.update(self.worker, responsable=self.manager.pk).status_code, 200)
        self.assertEqual(self.update(self.manager, responsable=self.worker.pk).status_code, 400)
        self.manager.refresh_from_db()
        self.assertIsNone(self.manager.responsable_id)
        inactive = self.employee("inactive")
        inactive.is_active = False
        inactive.save()
        self.assertEqual(self.update(self.worker, responsable=inactive.pk).status_code, 400)
        self.assertEqual(self.update(self.hr, responsable=self.worker.pk).status_code, 200)
        self.assertEqual(self.update(self.manager, responsable=self.hr.pk).status_code, 400)

    def test_employee_creation_accepts_manager_and_shared_position_titles(self):
        other = self.employee("other")
        position = Poste.objects.create(nom="Comptable")
        for employee in (self.worker, other):
            contrat_service.create({"employe": employee, "date_debut": "2020-01-01", "salaire_base": "200000", "heures_journalieres": "8", "poste": position}, actor=self.hr)
            self.assertEqual(self.client.get(reverse("employe-detail", args=[employee.pk])).data["poste_nom"], "Comptable")
        payload = self.payload(other, email="new-hierarchy@example.com", matricule="H-new", num_secu_sociale="H-new-SSN",
            password="TestSecure123!", responsable=self.manager.pk)
        response = self.client.post(reverse("employe-list"), payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["poste_nom"], "")
        self.assertEqual(response.data["responsable"], self.manager.pk)

    def test_directory_filters_current_contracts_and_position_without_duplicate_employees(self):
        today = timezone.localdate()
        cdi = TypeContrat.objects.create(type="CDI historique")
        cdd = TypeContrat.objects.create(type="CDD historique")
        position = Poste.objects.create(nom="Développeur")
        contract = Contrat.objects.create(employe=self.worker, poste=position, date_debut=today - timedelta(days=30), salaire_base="200000", heures_journalieres="8")
        contract.type.set([cdi, cdd])
        expired = Contrat.objects.create(employe=self.manager, date_debut=today - timedelta(days=90), date_fin=today - timedelta(days=1), salaire_base="100000", heures_journalieres="8")
        expired.type.add(cdi)
        response = self.client.get(reverse("employe-list"), {"poste": "développeur", "type_contrat": cdi.pk})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([item["id"] for item in response.data], [self.worker.pk])
        self.assertEqual({item["id"] for item in response.data[0]["types_contrat_actuels"]}, {cdi.pk, cdd.pk})
        self.assertNotIn("salaire_base", response.data[0])
        by_type = self.client.get(reverse("employe-list"), {"type_contrat": cdi.pk})
        self.assertEqual([item["id"] for item in by_type.data], [self.worker.pk])
        self.assertEqual(self.client.get(reverse("employe-list"), {"type_contrat": "invalid"}).status_code, 400)

    def test_contract_changes_types_and_deletion_preserve_history(self):
        first = TypeContrat.objects.create(type="CDD test historique")
        second = TypeContrat.objects.create(type="CDI test historique")
        payload = {"employe": self.worker.pk, "date_debut": "2026-01-01", "salaire_base": "200000.00", "heures_journalieres": "8", "type": [first.pk]}
        created = self.client.post(reverse("contrat-list"), payload, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        endpoint = reverse("contrat-detail", args=[created.data["id"]])
        updated = self.client.put(endpoint, {**payload, "salaire_base": "250000.00", "type": [second.pk]}, format="json")
        self.assertEqual(updated.status_code, 200, updated.data)
        history = EmployeHistorique.objects.filter(employe=self.worker, categorie="CONTRAT").first()
        self.assertEqual(history.avant["salaire_base"], "200000.00")
        self.assertEqual(history.apres["salaire_base"], "250000.00")
        self.assertEqual(history.apres["types_contrat"][0]["libelle"], second.type)
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker, categorie="CONTRAT").count(), 3)
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker).first().operation, "SUPPRESSION")

    def test_history_requires_directory_read_and_contract_history_requires_contract_read(self):
        position = Poste.objects.create(nom="Analyste")
        contrat_service.create({"employe": self.worker, "poste": position, "date_debut": "2026-01-01", "salaire_base": "123456", "heures_journalieres": "8"}, actor=self.hr)
        role = Role.objects.create(nom="HISTORY_DIRECTORY_ONLY")
        role.permissions.add(get_permission_by_code("employe.read"))
        self.manager.roles.add(role)
        self.client.force_authenticate(self.manager)
        endpoint = reverse("employee-history", args=[self.worker.pk])
        response = self.client.get(endpoint)
        self.assertEqual({row["categorie"] for row in response.data}, {"POSTE"})
        self.assertNotIn("123456", str(response.data))
        self.assertEqual(self.client.post(endpoint, {}, format="json").status_code, 403)
        self.client.force_authenticate(self.worker)
        self.assertEqual(self.client.get(endpoint).status_code, 403)
        self.assertEqual(self.update(self.worker, responsable=self.manager.pk).status_code, 403)

    def test_history_failure_rolls_back_position_and_employee_changes(self):
        with patch("core.services.employe_history_service.EmployeHistorique.objects.create", side_effect=RuntimeError("Unavailable")):
            with self.assertRaises(RuntimeError):
                employe_service.update(self.worker.pk, {"nom": "Rollback", "responsable": self.manager}, actor=self.hr)
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.nom, "Test")
        self.assertIsNone(self.worker.responsable_id)

    def test_directory_without_position_returns_editable_empty_string(self):
        response = self.client.get(reverse("employe-detail", args=[self.worker.pk]))
        self.assertEqual(response.data["poste_nom"], "")
        self.assertEqual(response.data["responsable_nom"], "")

    def test_contract_type_link_changes_are_also_historized(self):
        role = Role.objects.create(nom="HISTORY_LINK_EDITOR")
        role.permissions.add(*[get_permission_by_code(f"contrat_type_contrat.{action}") for action in ("create", "update", "delete")])
        self.hr.roles.add(role)
        contract = Contrat.objects.create(employe=self.worker, date_debut="2026-01-01", salaire_base="200000", heures_journalieres="8")
        first = TypeContrat.objects.create(type="Initial link type")
        second = TypeContrat.objects.create(type="Replacement link type")
        created = self.client.post(reverse("contrat-type-list"), {"contrat": contract.pk, "type_contrat": first.pk}, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        endpoint = reverse("contrat-type-detail", args=[created.data["id"]])
        self.assertEqual(self.client.put(endpoint, {"contrat": contract.pk, "type_contrat": second.pk}, format="json").status_code, 200)
        history = EmployeHistorique.objects.filter(employe=self.worker).first()
        self.assertEqual(history.avant["types_contrat"][0]["id"], first.pk)
        self.assertEqual(history.apres["types_contrat"][0]["id"], second.pk)
        self.assertEqual(self.client.delete(endpoint).status_code, 204)
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker).count(), 3)
        self.assertEqual(EmployeHistorique.objects.filter(employe=self.worker).first().apres["types_contrat"], [])
