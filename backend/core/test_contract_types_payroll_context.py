from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Contrat, Employe, Role, TypeContrat
from core.permission_codes import get_permission_by_code
from core.services.contrat_service import contrat_service


class ContractTypePayrollContextTests(APITestCase):
    def setUp(self):
        self.employee = Employe.objects.create_user(
            email="contract-context@example.com", password=None, matricule="CONTEXT-001",
            num_secu_sociale="CONTEXT-SSN-001", nom="Test", prenom="Contexte", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )
        self.client.force_authenticate(self.employee)

    def grant(self, *codes):
        role = Role.objects.create(nom="CONTEXT-TEST")
        role.permissions.set([get_permission_by_code(code) for code in codes])
        self.employee.roles.add(role)

    def contract(self, **changes):
        return Contrat.objects.create(employe=self.employee, date_debut="2026-01-01", salaire_base="325000.50", heures_journalieres="8", **changes)

    def context(self, **changes):
        return self.client.get(reverse("paie-contexte-contrat"), {"employe": self.employee.pk, "periode": "2026-10", **changes})

    def test_contract_types_crud_is_available_to_module_one_profile(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES"))
        response = self.client.post(reverse("type-contrat-list"), {"type": "CDD test", "description": "Contrat temporaire"}, format="json")
        self.assertEqual(response.status_code, 201)
        url = reverse("type-contrat-detail", args=[response.data["id"]])
        self.assertEqual(self.client.put(url, {"type": "CDD corrigé", "description": "Mise à jour"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_used_contract_type_cannot_be_deleted_and_assignment_is_preserved(self):
        self.grant("type_contrat.delete")
        contract_type = TypeContrat.objects.create(type="CDI protégé")
        contract = self.contract()
        contract.type.add(contract_type)
        response = self.client.delete(reverse("type-contrat-detail", args=[contract_type.pk]))
        self.assertEqual(response.status_code, 400)
        self.assertIn("utilisé", str(response.data))
        self.assertTrue(contract.type.filter(pk=contract_type.pk).exists())

    def test_read_only_contract_type_role_cannot_create(self):
        self.grant("type_contrat.read")
        self.assertEqual(self.client.get(reverse("type-contrat-list")).status_code, 200)
        self.assertEqual(self.client.post(reverse("type-contrat-list"), {"type": "Interdit"}, format="json").status_code, 403)

    def test_payroll_context_requires_payroll_read_permission(self):
        self.grant("contrat.read")
        self.contract()
        self.assertEqual(self.context().status_code, 403)

    def test_payroll_reader_sees_contract_attributes_without_contract_crud_rights(self):
        self.grant("paie.read")
        contract_type = TypeContrat.objects.create(type="CDI contexte")
        contract = self.contract()
        contract.type.add(contract_type)
        response = self.context()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], "READY")
        detail = response.data["contracts"][0]
        self.assertEqual(detail["salaire_base"], "325000.50")
        self.assertEqual(detail["heures_journalieres"], "8.00")
        self.assertEqual(detail["types_libelles"], ["CDI contexte"])
        self.assertEqual(detail["statut"], "EN_COURS")
        self.assertEqual(detail["date_debut"], "2026-01-01")
        self.assertEqual(self.client.get(reverse("contrat-list")).status_code, 403)

    def test_context_distinguishes_absent_partial_and_overlapping_contracts(self):
        self.grant("paie.read")
        self.assertEqual(self.context().data["state"], "MISSING")
        first = self.contract(date_fin="2026-10-10")
        self.assertEqual(self.context().data["state"], "READY")
        Contrat.objects.create(employe=self.employee, date_debut="2026-10-11", salaire_base="400000", heures_journalieres="7")
        response = self.context()
        self.assertEqual(response.data["state"], "AMBIGUOUS")
        self.assertEqual(len(response.data["contracts"]), 2)
        self.assertEqual(self.context(periode="2025-10").data["state"], "MISSING")
        self.assertEqual(self.context(periode="2026-09").data["contracts"][0]["id"], first.pk)

    def test_context_rejects_invalid_employee_period_and_zero_year(self):
        self.grant("paie.read")
        for changes in ({"employe": "no"}, {"employe": 0}, {"periode": "2026-13"}, {"periode": "0000-01"}, {"periode": "2026-1"}):
            self.assertEqual(self.context(**changes).status_code, 400)

    def test_context_prefetches_multiple_contract_type_labels(self):
        self.grant("paie.read")
        first = self.contract(date_fin="2026-10-10")
        second = Contrat.objects.create(employe=self.employee, date_debut="2026-10-11", salaire_base="400000", heures_journalieres="8")
        kind = TypeContrat.objects.create(type="Type partagé")
        first.type.add(kind)
        second.type.add(kind)
        with self.assertNumQueries(2):
            context = contrat_service.payroll_context(self.employee.pk, "2026-10")
            self.assertEqual([list(item.type.all())[0].type for item in context["contracts"]], ["Type partagé", "Type partagé"])
