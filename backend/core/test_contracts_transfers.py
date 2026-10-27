from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Contrat, Employe, OrdreVirement, Paie, Role, TypeContrat
from core.permission_codes import get_permission_by_code, permission_code


class ContractsTransfersApiTests(APITestCase):
    def setUp(self):
        self.employee = self.employee_for("ONE")
        self.other = self.employee_for("TWO")
        self.client.force_authenticate(self.employee)

    def employee_for(self, suffix):
        return Employe.objects.create_user(
            email=f"contract-transfer-{suffix}@example.com", password=None,
            nom="Test", prenom=suffix, matricule=f"CT-{suffix}", num_secu_sociale=f"CT-SSN-{suffix}",
            date_naissance="1990-01-01", date_entree="2020-01-01", adresse="Test", telephone="0000",
        )

    def grant(self, *codes):
        role = Role.objects.create(nom="CONTRACT-TRANSFER-TEST")
        role.permissions.set([get_permission_by_code(code) for code in codes])
        self.employee.roles.add(role)

    def contract_payload(self, **changes):
        return {"employe": self.employee.pk, "date_debut": "2026-01-01", "date_fin": None,
                "salaire_base": "300000.00", "heures_journalieres": "8.00", "statut": "EN_COURS", **changes}

    def test_contract_profile_can_create_modify_filter_and_delete_contract(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES"))
        contract_type = TypeContrat.objects.create(type="CDI test")
        payload = self.contract_payload(type=[contract_type.pk])
        created = self.client.post(reverse("contrat-list"), payload, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["types_libelles"], ["CDI test"])
        Contrat.objects.create(employe=self.other, date_debut="2026-01-01", salaire_base="10", heures_journalieres="8")
        listed = self.client.get(reverse("contrat-list"), {"employe": self.employee.pk})
        self.assertEqual([item["id"] for item in listed.data], [created.data["id"]])
        url = reverse("contrat-detail", args=[created.data["id"]])
        self.assertEqual(self.client.put(url, {**payload, "salaire_base": "310000"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_contract_rejects_dates_salary_hours_and_reassignment(self):
        self.grant("contrat.create", "contrat.update", "contrat.read")
        for change, field in (({"date_fin": "2025-12-31"}, "date_fin"), ({"salaire_base": "-1"}, "salaire_base"),
                              ({"heures_journalieres": "25"}, "heures_journalieres")):
            response = self.client.post(reverse("contrat-list"), self.contract_payload(**change), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data)
        created = self.client.post(reverse("contrat-list"), self.contract_payload(), format="json")
        response = self.client.put(reverse("contrat-detail", args=[created.data["id"]]), self.contract_payload(employe=self.other.pk), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("employe", response.data)
        self.assertEqual(self.client.get(reverse("contrat-list"), {"employe": "invalid"}).status_code, 400)

    def test_read_only_contract_permission_cannot_write(self):
        self.grant("contrat.read")
        self.assertEqual(self.client.get(reverse("contrat-list")).status_code, 200)
        self.assertEqual(self.client.post(reverse("contrat-list"), self.contract_payload(), format="json").status_code, 403)

    def order(self, **changes):
        Paie.objects.get_or_create(employe=self.employee, periode="2026-10", defaults={"libelle": "Paie pour ordre", "statut": "VALIDEE"})
        return OrdreVirement.objects.create(employe=self.employee, periode="2026-10", date_generation="2026-10-23T12:00:00Z", **changes)

    def test_transfer_creator_cannot_decide_without_update_permission(self):
        self.grant("ordre_virement.create", "ordre_virement.read")
        Paie.objects.create(employe=self.employee, periode="2026-10", libelle="Test", statut="VALIDEE")
        created = self.client.post(reverse("ordre-virement-list"), {"employe": self.employee.pk, "periode": "2026-10"}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertIsNotNone(created.data["date_generation"])
        for route in ("ordre-virement-traiter", "ordre-virement-rejeter", "ordre-virement-annuler"):
            response = self.client.post(reverse(route, args=[created.data["id"]]), {"motif": "Test"}, format="json")
            self.assertEqual(response.status_code, 403)

    def test_update_permission_can_reject_with_audited_reason_and_allow_replacement(self):
        self.grant("ordre_virement.update", "ordre_virement.create")
        order = self.order()
        url = reverse("ordre-virement-rejeter", args=[order.pk])
        self.assertEqual(self.client.post(url, {}, format="json").status_code, 400)
        rejected = self.client.post(url, {"motif": "Coordonnées à vérifier"}, format="json")
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(rejected.data["statut"], "REJETE")
        self.assertEqual(rejected.data["decideur"], self.employee.pk)
        self.assertEqual(rejected.data["motif_decision"], "Coordonnées à vérifier")
        self.assertIsNotNone(rejected.data["date_decision"])
        self.assertEqual(self.client.post(url, {"motif": "Encore"}, format="json").status_code, 400)
        replacement = self.client.post(reverse("ordre-virement-list"), {"employe": self.employee.pk, "periode": "2026-10"}, format="json")
        self.assertEqual(replacement.status_code, 201)

    def test_order_requires_validated_payroll(self):
        self.grant("ordre_virement.create")
        payload = {"employe": self.employee.pk, "periode": "2026-10"}
        self.assertEqual(self.client.post(reverse("ordre-virement-list"), payload, format="json").status_code, 400)
        payroll = Paie.objects.create(employe=self.employee, periode="2026-10", libelle="Test")
        self.assertEqual(self.client.post(reverse("ordre-virement-list"), payload, format="json").status_code, 400)
        payroll.statut = "VALIDEE"
        payroll.save()
        self.assertEqual(self.client.post(reverse("ordre-virement-list"), payload, format="json").status_code, 201)

    def test_transfer_duplicate_is_rejected_and_generation_date_preserved_on_update(self):
        self.grant("ordre_virement.create", "ordre_virement.update")
        order = self.order()
        payload = {"employe": self.employee.pk, "periode": "2026-10"}
        duplicate = self.client.post(reverse("ordre-virement-list"), payload, format="json")
        self.assertEqual(duplicate.status_code, 400)
        updated = self.client.put(reverse("ordre-virement-detail", args=[order.pk]), payload, format="json")
        self.assertEqual(updated.status_code, 200, updated.data)
        order.refresh_from_db()
        self.assertEqual(order.date_generation.isoformat(), "2026-10-23T12:00:00+00:00")

    def test_module_profile_records_treatment_then_associates_paid_payroll(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS"))
        payroll = Paie.objects.create(employe=self.employee, periode="2026-10", libelle="Test", statut="VALIDEE")
        order = self.order()
        treated = self.client.post(reverse("ordre-virement-traiter", args=[order.pk]), {"motif": "Traitement enregistré"}, format="json")
        self.assertEqual(treated.status_code, 200)
        paid = self.client.post(reverse("paie-marquer-payee", args=[payroll.pk]), {"ordre_virement": order.pk}, format="json")
        self.assertEqual(paid.status_code, 200, paid.data)
        self.assertEqual(paid.data["statut"], "PAYE")
        self.assertEqual(paid.data["ordre_virement"], order.pk)
        self.assertIsNotNone(paid.data["date_paiement"])
        self.assertEqual(self.client.delete(reverse("ordre-virement-detail", args=[order.pk])).status_code, 400)

    def test_profiles_cover_only_their_modules_and_remain_unassigned(self):
        one = Role.objects.get(nom="FRONTEND_MODULE_1_EMPLOYES_ACCES")
        four = Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS")
        codes = lambda role: {permission_code(item) for item in role.permissions.select_related("content_type")}
        self.assertEqual(len(codes(one)), 26)
        self.assertTrue({"poste.read", "poste.create", "poste.update", "poste.delete"}.issubset(codes(one)))
        self.assertTrue({"contrat.read", "contrat.create", "contrat.update", "contrat.delete", "type_contrat.read"}.issubset(codes(one)))
        self.assertEqual(len(codes(four)), 10)
        self.assertFalse(Employe.objects.filter(roles__in=[one, four]).exists())
