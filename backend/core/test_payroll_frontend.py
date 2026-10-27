from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Employe, Paie, Role
from core.permission_codes import get_permission_by_code, permission_code
from core.repositories.paie_repository import PaieRepository
from core.serializers.paie_serializer import PaieSerializer


class PayrollFrontendRoleTests(TestCase):
    def test_module_profile_has_payroll_transfer_crud_and_employee_read(self):
        role = Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS")
        codes = {permission_code(item) for item in role.permissions.select_related("content_type")}
        self.assertEqual(codes, {"paie.read", "paie.create", "paie.update", "paie.delete", "employe.read",
                                 "ordre_virement.read", "ordre_virement.create", "ordre_virement.update", "ordre_virement.delete", "ordre_virement.generate_document"})
        self.assertFalse(Employe.objects.filter(roles=role).exists())


class PayrollFrontendApiTests(APITestCase):
    def setUp(self):
        self.employee = Employe.objects.create_user(
            email="payroll-frontend@example.com", password="test-only-password",
            nom="Test", prenom="Paie", matricule="PAY-UI-001",
            num_secu_sociale="PAY-UI-SSN-001", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )
        self.payroll = Paie.objects.create(employe=self.employee, periode="2026-10", libelle="Test paie")
        self.client.force_authenticate(self.employee)

    def grant(self, *codes):
        role = Role.objects.create(nom="PAYROLL-UI-TEST")
        role.permissions.set([get_permission_by_code(code) for code in codes])
        self.employee.roles.add(role)

    def test_employee_without_payroll_permissions_cannot_list_or_decide(self):
        self.assertEqual(self.client.get(reverse("paie-list")).status_code, 403)
        self.assertEqual(self.client.post(reverse("paie-valider", args=[self.payroll.pk])).status_code, 403)

    def test_read_only_role_can_consult_identity_but_cannot_mutate(self):
        self.grant("paie.read")
        response = self.client.get(reverse("paie-detail", args=[self.payroll.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["employe_matricule"], "PAY-UI-001")
        self.assertEqual(response.data["employe_nom"], "Test")
        for route in ("paie-calculer", "paie-valider", "paie-annuler", "paie-bulletin"):
            self.assertEqual(self.client.post(reverse(route, args=[self.payroll.pk]), {}, format="json").status_code, 403)

    def test_employee_identity_is_read_only_in_update(self):
        self.grant("paie.update")
        response = self.client.put(reverse("paie-detail", args=[self.payroll.pk]), {
            "employe": self.employee.pk, "periode": "2026-10", "libelle": "Modifiée",
            "employe_nom": "Faux", "employe_matricule": "Faux",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["employe_nom"], "Test")
        self.assertEqual(response.data["employe_matricule"], "PAY-UI-001")
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.nom, "Test")

    def test_identity_is_loaded_with_payroll_without_extra_queries(self):
        with self.assertNumQueries(1):
            data = PaieSerializer(PaieRepository().get(self.payroll.pk)).data
            self.assertEqual(data["employe_prenom"], "Paie")

    def test_module_profile_can_prepare_and_remove_draft_without_other_roles(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS"))
        self.assertEqual(self.client.get(reverse("employe-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("regle-paie-list")).status_code, 200)
        payload = {"employe": self.employee.pk, "periode": "2026-11", "libelle": "Brouillon novembre"}
        created = self.client.post(reverse("paie-list"), payload, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["statut"], "BROUILLON")
        detail_url = reverse("paie-detail", args=[created.data["id"]])
        updated = self.client.put(detail_url, {**payload, "libelle": "Brouillon corrigé"}, format="json")
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(self.client.delete(detail_url).status_code, 204)

    def rule_payload(self):
        return {
            "code": "RULE-API-TEST", "nom": "Règles de test isolé", "date_debut": "2026-01-01",
            "heures_mensuelles": "160", "plafond_cnss": "1000000",
            "taux_cnss_salarial": "0.01", "taux_cnss_patronal": "0.02", "taux_tpa_patronal": "0.03",
            "abattement_professionnel": "0.10", "plafond_deduction_retraite": "0.05",
            "tranches_iuts": [{"minimum": "0", "maximum": None, "taux": "0.10"}],
            "reductions_iuts_charges": [], "source_reference": "Référence de test isolé",
        }

    def test_rule_creation_requires_reference_and_separate_validation(self):
        self.employee.roles.add(Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS"))
        invalid = self.client.post(reverse("regle-paie-list"), {**self.rule_payload(), "source_reference": ""}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("source_reference", invalid.data)
        created = self.client.post(reverse("regle-paie-list"), self.rule_payload(), format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertNotIn("est_fictif", created.data)
        self.assertFalse(created.data["valide"])
        blocked = self.client.post(reverse("paie-calculer", args=[self.payroll.pk]), {"regle_paie": created.data["id"]}, format="json")
        self.assertEqual(blocked.status_code, 400)
        self.assertIn("regle_paie", blocked.data)
        validated = self.client.post(reverse("regle-paie-valider", args=[created.data["id"]]), {}, format="json")
        self.assertEqual(validated.status_code, 200)
        self.assertTrue(validated.data["valide"])
        changed = self.client.put(reverse("regle-paie-detail", args=[created.data["id"]]), {**self.rule_payload(), "nom": "Changement"}, format="json")
        self.assertEqual(changed.status_code, 400)

    def test_rule_creation_and_validation_are_denied_to_read_only_role(self):
        from core.models import ReglePaie

        self.grant("paie.read")
        rule = ReglePaie.objects.create(**self.rule_payload())
        self.assertEqual(self.client.post(reverse("regle-paie-list"), self.rule_payload(), format="json").status_code, 403)
        self.assertEqual(self.client.post(reverse("regle-paie-valider", args=[rule.pk]), {}, format="json").status_code, 403)

    def test_old_payroll_without_snapshot_cannot_offer_bulletin_generation(self):
        from django.utils import timezone

        self.grant("paie.read")
        self.payroll.statut = "VALIDEE"
        self.payroll.date_calcul = timezone.now()
        self.payroll.save()
        detail = self.client.get(reverse("paie-detail", args=[self.payroll.pk]))
        self.assertFalse(detail.data["bulletin_generable"])
        self.payroll.detail_calcul = {"totaux": {"salaire_net": "100"}}
        self.payroll.save()
        detail = self.client.get(reverse("paie-detail", args=[self.payroll.pk]))
        self.assertTrue(detail.data["bulletin_generable"])

    def test_missing_bulletin_file_returns_readable_not_found_error(self):
        self.grant("paie.read")
        self.payroll.bulletin_pdf = "bulletins/nonexistent-test-file.pdf"
        self.payroll.save()
        response = self.client.get(reverse("paie-bulletin", args=[self.payroll.pk]), HTTP_ACCEPT="*/*")
        self.assertEqual(response.status_code, 404)
        self.assertIn("introuvable", response.data["detail"])
