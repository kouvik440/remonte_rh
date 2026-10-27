from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import AffectationProjet, Contrat, Employe, FeuilleTemps, Paie, Projet, Role, TacheProjet
from core.permission_codes import get_permission_by_code


class TimesheetWorkflowTests(APITestCase):
    def setUp(self):
        self.employee = self.employee_user("EMP")
        self.manager = self.employee_user("MANAGER")
        role = Role.objects.create(nom="TIMESHEET_TEST_REVIEWER")
        role.permissions.add(get_permission_by_code("feuille_temps.decide"), get_permission_by_code("paie.read"))
        self.manager.roles.add(role)
        self.contract = Contrat.objects.create(employe=self.employee, date_debut=date(2026, 1, 1), salaire_base="220000", heures_journalieres="6")
        self.project = Projet.objects.create(code="TIMESHEET-UI", nom="Prestation")
        self.task = TacheProjet.objects.create(projet=self.project, code="ANALYSE", nom="Analyse")
        AffectationProjet.objects.create(projet=self.project, employe=self.employee)
        Paie.objects.create(employe=self.employee, periode="2026-10", statut="PAYE", salaire_brut="220000", cout_charge="264000")
        self.client.force_authenticate(self.employee)
        self.payload = {"semaine_debut": "2026-10-19", "lignes": [{"date_travail": "2026-10-20", "projet": self.project.pk, "tache": self.task.pk, "jours": "0.5", "commentaire": "Analyse du besoin"}]}

    @staticmethod
    def employee_user(suffix):
        return Employe.objects.create_user(email=f"timesheet-{suffix}@example.com", password=None,
            matricule=f"TIME-{suffix}", num_secu_sociale=f"TIME-SSN-{suffix}", nom="Test", prenom=suffix,
            date_naissance="1990-01-01", date_entree="2020-01-01", adresse="Test", telephone="0000")

    def create_sheet(self, payload=None):
        response = self.client.post(reverse("feuille-temps-list"), payload or self.payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def costs(self):
        return self.client.get(reverse("couts-projets"), {"date_debut": "2026-10-01", "date_fin": "2026-10-31"})

    def test_days_convert_using_contract_hours_and_totals_are_returned(self):
        sheet = self.create_sheet()
        self.assertEqual(sheet["lignes"][0]["heures"], "3.00")
        self.assertEqual(sheet["total_heures"], "3.00")
        self.assertEqual(sheet["jours_saisis"], 1)
        self.assertEqual(sheet["employe_matricule"], self.employee.matricule)

    def test_mixed_days_hours_cannot_exceed_daily_contract_limit(self):
        self.payload["lignes"].append({"date_travail": "2026-10-20", "projet": self.project.pk, "tache": self.task.pk, "heures": "3.01"})
        response = self.client.post(reverse("feuille-temps-list"), self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(FeuilleTemps.objects.exists())

    def test_line_requires_exactly_one_duration_unit(self):
        self.payload["lignes"][0]["heures"] = "1"
        self.assertEqual(self.client.post(reverse("feuille-temps-list"), self.payload, format="json").status_code, 400)
        del self.payload["lignes"][0]["heures"]
        del self.payload["lignes"][0]["jours"]
        self.assertEqual(self.client.post(reverse("feuille-temps-list"), self.payload, format="json").status_code, 400)

    def test_days_require_unambiguous_daily_schedule(self):
        self.contract.heures_journalieres = None
        self.contract.save()
        self.assertEqual(self.client.post(reverse("feuille-temps-list"), self.payload, format="json").status_code, 400)
        self.contract.heures_journalieres = Decimal("6")
        self.contract.save()
        Contrat.objects.create(employe=self.employee, date_debut="2026-10-01", salaire_base="100", heures_journalieres="4")
        self.assertEqual(self.client.post(reverse("feuille-temps-list"), self.payload, format="json").status_code, 400)

    def test_employee_cannot_see_approval_queue_or_payroll_costs(self):
        self.assertEqual(self.client.get(reverse("feuille-temps-a-valider")).status_code, 403)
        self.assertEqual(self.costs().status_code, 403)
        self.assertEqual(self.client.get(reverse("feuille-temps-projets")).status_code, 200)

    def test_full_submission_approval_cost_and_correction_cycle(self):
        sheet = self.create_sheet()
        endpoint = reverse("feuille-temps-detail", args=[sheet["id"]])
        self.assertEqual(self.client.post(reverse("feuille-temps-soumettre", args=[sheet["id"]])).status_code, 200)
        self.assertEqual(self.client.put(endpoint, self.payload, format="json").status_code, 400)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.costs().data["rapprochement"], [])
        approved = self.client.post(reverse("feuille-temps-valider", args=[sheet["id"]]))
        self.assertEqual(approved.status_code, 200, approved.data)
        self.assertEqual(approved.data["valideur_prenom"], "MANAGER")
        reconciliation = self.costs().data["rapprochement"][0]
        self.assertEqual(reconciliation["heures_validees"], "3.00")
        self.assertEqual(reconciliation["taux_horaire_charge"], "2000.00")
        self.assertEqual(reconciliation["cout_estime"], "6000.00")
        self.assertEqual(reconciliation["periode"], "2026-10")
        self.client.force_authenticate(self.employee)
        edited = self.client.put(endpoint, self.payload, format="json")
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.data["statut"], "BROUILLON")
        self.assertIsNone(edited.data["valideur"])
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.costs().data["rapprochement"], [])

    def test_refusal_returns_draft_with_reason_and_can_be_resubmitted(self):
        sheet = self.create_sheet()
        self.client.post(reverse("feuille-temps-soumettre", args=[sheet["id"]]))
        self.client.force_authenticate(self.manager)
        endpoint = reverse("feuille-temps-refuser", args=[sheet["id"]])
        self.assertEqual(self.client.post(endpoint, {"motif": " "}, format="json").status_code, 400)
        response = self.client.post(endpoint, {"motif": "Préciser le commentaire"}, format="json")
        self.assertEqual(response.data["statut"], "BROUILLON")
        self.assertEqual(response.data["motif_refus"], "Préciser le commentaire")
        self.client.force_authenticate(self.employee)
        response = self.client.post(reverse("feuille-temps-soumettre", args=[sheet["id"]]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["motif_refus"], "")

    def test_other_employee_cannot_read_update_delete_or_submit_sheet(self):
        sheet = self.create_sheet()
        self.client.force_authenticate(self.manager)
        endpoint = reverse("feuille-temps-detail", args=[sheet["id"]])
        self.assertEqual(self.client.get(endpoint).status_code, 404)
        self.assertEqual(self.client.put(endpoint, self.payload, format="json").status_code, 404)
        self.assertEqual(self.client.delete(endpoint).status_code, 404)
        self.assertEqual(self.client.post(reverse("feuille-temps-soumettre", args=[sheet["id"]])).status_code, 404)

    def test_empty_draft_is_allowed_but_cannot_be_submitted(self):
        sheet = self.create_sheet({"semaine_debut": "2026-10-19", "lignes": []})
        self.assertEqual(sheet["total_heures"], "0.00")
        self.assertEqual(self.client.post(reverse("feuille-temps-soumettre", args=[sheet["id"]])).status_code, 400)

    def test_duration_and_calendar_limits_return_validation_errors(self):
        for days in ("0", "-0.5", "1.01", "0.001"):
            self.payload["lignes"][0]["jours"] = days
            self.assertEqual(self.client.post(reverse("feuille-temps-list"), self.payload, format="json").status_code, 400)
        response = self.client.post(reverse("feuille-temps-list"), {"semaine_debut": "9999-12-27", "lignes": []}, format="json")
        self.assertEqual(response.status_code, 400)
