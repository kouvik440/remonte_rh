from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Contrat, CoordonneesBancaires, DemandeAbsence, Employe, Role, TypeConge
from core.permission_codes import permission_code


class RemainingRoleProfilesTests(TestCase):
    def test_new_roles_have_the_permissions_required_by_their_screens(self):
        expected = {
            "EMPLOYE_SIMPLE": {"conge.read", "demande_absence.read", "demande_absence.create", "solde_conge.read",
                "coordonnees_bancaires.read", "coordonnees_bancaires.create", "coordonnees_bancaires.update"},
            "FRONTEND_MODULE_6_TGM": {"paie.read"},
            "FRONTEND_MODULE_7_FEUILLES_TEMPS": {"feuille_temps.decide", "projet.read", "projet.create", "projet.assign_employees", "tache.read", "tache.create", "tache.delete", "employe.read"},
        }
        for name, codes in expected.items():
            role = Role.objects.get(nom=name)
            self.assertEqual({permission_code(permission) for permission in role.permissions.select_related("content_type")}, codes)
            self.assertFalse(Employe.objects.filter(roles=role).exists())


class SimpleEmployeeAccessTests(APITestCase):
    def setUp(self):
        self.awa = self.employee("AWA")
        self.moussa = self.employee("MOUSSA")
        role = Role.objects.get(nom="EMPLOYE_SIMPLE")
        self.awa.roles.add(role)
        self.moussa.roles.add(role)
        self.client.force_authenticate(self.awa)

    @staticmethod
    def employee(suffix):
        return Employe.objects.create_user(email=f"role-{suffix}@example.com", password=None, nom="Test", prenom=suffix,
            matricule=f"ROLE-{suffix}", num_secu_sociale=f"ROLE-SSN-{suffix}", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000")

    def test_employee_can_read_personal_modules_and_has_no_global_access(self):
        for name in ("demande-absence-list", "solde-conge-list", "conge-type-list", "coordonnees-bancaires-list", "feuille-temps-list", "feuille-temps-projets"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        for name in ("employe-list", "role-list", "permission-list", "paie-list", "projet-list", "feuille-temps-a-valider"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403, name)
        self.assertEqual(self.client.get(reverse("tgm-list"), {"periode_debut": "2026-01", "periode_fin": "2026-12"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("masse-salariale"), {"periode_debut": "2026-01", "periode_fin": "2026-12"}).status_code, 403)

    def test_absence_and_balances_are_personal_and_cannot_be_approved_or_deleted(self):
        leave_type = TypeConge.objects.create(code="ROLE-CP", libelle="Congé", jours_par_annee=30)
        Contrat.objects.create(employe=self.awa, date_debut="2026-01-01", salaire_base="220000", heures_journalieres="6")
        other = DemandeAbsence.objects.create(employe=self.moussa, type_conge=leave_type, date_debut="2026-10-26", date_fin="2026-10-26")
        response = self.client.post(reverse("demande-absence-list"), {"type_conge": leave_type.pk, "date_debut": "2026-11-02", "date_fin": "2026-11-02", "motif": "Test", "employe": self.moussa.pk}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["employe"], self.awa.pk)
        own_id = response.data["id"]
        self.assertEqual([row["id"] for row in self.client.get(reverse("demande-absence-list")).data], [own_id])
        self.assertEqual(self.client.get(reverse("demande-absence-detail", args=[other.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("demande-absence-valider", args=[own_id])).status_code, 403)
        self.assertEqual(self.client.delete(reverse("demande-absence-detail", args=[own_id])).status_code, 403)
        for row in self.client.get(reverse("solde-conge-list"), {"annee": 2026, "employe": self.moussa.pk}).data:
            self.assertEqual(row["employe"], self.awa.pk)

    def test_employee_can_work_on_own_timesheets_but_not_another_employees(self):
        response = self.client.post(reverse("feuille-temps-list"), {"semaine_debut": "2026-10-19", "lignes": []}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        sheet_id = response.data["id"]
        self.client.force_authenticate(self.moussa)
        self.assertEqual(self.client.get(reverse("feuille-temps-list")).data, [])
        self.assertEqual(self.client.get(reverse("feuille-temps-detail", args=[sheet_id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("feuille-temps-valider", args=[sheet_id])).status_code, 403)
        self.client.force_authenticate(self.awa)
        self.assertEqual(self.client.delete(reverse("feuille-temps-detail", args=[sheet_id])).status_code, 204)

    def test_personal_bank_permissions_do_not_expose_or_reassign_other_accounts(self):
        other = CoordonneesBancaires.objects.create(employe=self.moussa, iban="TEST-IBAN-MOUSSA", banque="Test")
        response = self.client.post(reverse("coordonnees-bancaires-list"), {"iban": "TEST-IBAN-AWA", "banque": "Test", "employe": self.moussa.pk}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["employe"], self.awa.pk)
        self.assertEqual([row["id"] for row in self.client.get(reverse("coordonnees-bancaires-list")).data], [response.data["id"]])
        self.assertEqual(self.client.get(reverse("coordonnees-bancaires-detail", args=[other.pk])).status_code, 403)
        self.assertEqual(self.client.put(reverse("coordonnees-bancaires-detail", args=[other.pk]), {"iban": "TEST-IBAN-CHANGED", "banque": "Test"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(reverse("coordonnees-bancaires-detail", args=[response.data["id"]])).status_code, 403)

    def test_tgm_role_reads_costs_but_does_not_grant_write_or_timesheet_decisions(self):
        self.awa.roles.set([Role.objects.get(nom="FRONTEND_MODULE_6_TGM")])
        self.assertEqual(self.client.get(reverse("tgm-list"), {"periode_debut": "2026-01", "periode_fin": "2026-12"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("couts-projets"), {"date_debut": "2026-01-01", "date_fin": "2026-12-31"}).status_code, 200)
        self.assertEqual(self.client.post(reverse("paie-list"), {}, format="json").status_code, 403)
        self.assertEqual(self.client.get(reverse("feuille-temps-a-valider")).status_code, 403)

    def test_timesheet_manager_can_prepare_projects_and_decide_but_cannot_read_payroll(self):
        self.awa.roles.set([Role.objects.get(nom="FRONTEND_MODULE_7_FEUILLES_TEMPS")])
        self.assertEqual(self.client.get(reverse("feuille-temps-a-valider")).status_code, 200)
        created = self.client.post(reverse("projet-list"), {"code": "ROLE-PROJET", "nom": "Projet"}, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        project_id = created.data["id"]
        self.assertEqual(self.client.post(reverse("projet-tache-list", args=[project_id]), {"code": "ROLE-TACHE", "nom": "Tâche"}, format="json").status_code, 201)
        self.assertEqual(self.client.post(reverse("projet-affectation-list", args=[project_id]), {"employe": self.moussa.pk}, format="json").status_code, 201)
        self.assertEqual(self.client.get(reverse("paie-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("couts-projets"), {"date_debut": "2026-01-01", "date_fin": "2026-12-31"}).status_code, 403)
