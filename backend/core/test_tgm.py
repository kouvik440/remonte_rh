from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Contrat, Employe, FeuilleTemps, LigneFeuilleTemps, Paie, Projet, Role, TacheProjet
from core.permission_codes import get_permission_by_code
from core.services.tgm_service import tgm_service


class TgmApiTests(APITestCase):
    def setUp(self):
        self.employee = Employe.objects.create_user(
            email="tgm@example.com", password=None, nom="Test", prenom="TGM",
            matricule="TGM-001", num_secu_sociale="TGM-SSN", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )
        self.role = Role.objects.create(nom="TGM_READER_TEST")
        self.role.permissions.add(get_permission_by_code("paie.read"))
        self.employee.roles.add(self.role)
        self.client.force_authenticate(self.employee)
        self.contract = Contrat.objects.create(
            employe=self.employee, date_debut=date(2026, 1, 1), salaire_base="220000", heures_journalieres="6",
        )
        self.payroll = Paie.objects.create(
            employe=self.employee, periode="2026-10", statut="VALIDEE", salaire_brut="220000", cout_charge="264000",
        )
        self.query = {"periode_debut": "2026-10", "periode_fin": "2026-10"}

    def report(self, **params):
        return self.client.get(reverse("tgm-list"), {**self.query, **params})

    def row(self):
        response = self.report()
        self.assertEqual(response.status_code, 200, response.data)
        return response.data["employes"][0]

    def time_line(self, hours="2", status="VALIDEE"):
        project, _ = Projet.objects.get_or_create(code="TGM-PROJET", defaults={"nom": "Prestation"})
        task, _ = TacheProjet.objects.get_or_create(projet=project, code="TGM-TACHE", defaults={"nom": "Analyse"})
        sheet = FeuilleTemps.objects.create(employe=self.employee, semaine_debut=date(2026, 10, 19), statut=status)
        return LigneFeuilleTemps.objects.create(
            feuille=sheet, projet=project, tache=task, date_travail=date(2026, 10, 20), heures=hours,
        )

    def costs(self):
        response = self.client.get(reverse("couts-projets"), {"date_debut": "2026-10-01", "date_fin": "2026-10-31"})
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def test_daily_and_hourly_rates_follow_six_hour_contract(self):
        row = self.row()
        self.assertEqual(row["jours_ouvres_previsionnels"], 22)
        self.assertEqual(row["heures_previsionnelles"], "132.00")
        self.assertEqual(row["taux_journalier_brut"], "10000.00")
        self.assertEqual(row["taux_journalier_charge"], "12000.00")
        self.assertEqual(row["taux_horaire_brut"], "1666.67")
        self.assertEqual(row["taux_horaire_charge"], "2000.00")

    def test_missing_schedule_keeps_daily_rate_but_not_hourly(self):
        self.contract.heures_journalieres = None
        self.contract.save()
        row = self.row()
        self.assertEqual(row["taux_journalier_charge"], "12000.00")
        self.assertIsNone(row["taux_horaire_charge"])
        self.assertIsNone(row["heures_previsionnelles"])
        self.assertTrue(row["motif_indisponibilite_horaire"])

    def test_overlapping_contracts_do_not_double_days_or_guess_hours(self):
        Contrat.objects.create(employe=self.employee, date_debut="2026-10-15", salaire_base="100", heures_journalieres="4")
        row = self.row()
        self.assertEqual(row["jours_ouvres_previsionnels"], 22)
        self.assertIsNone(row["taux_horaire_charge"])

    def test_schedule_change_within_month_sums_each_days_hours(self):
        self.contract.date_fin = date(2026, 10, 15)
        self.contract.save()
        Contrat.objects.create(employe=self.employee, date_debut="2026-10-16", salaire_base="100", heures_journalieres="4")
        self.assertEqual(self.row()["heures_previsionnelles"], "110.00")

    def test_missing_contract_or_amount_never_produces_zero_rate(self):
        self.contract.delete()
        self.payroll.cout_charge = None
        self.payroll.save()
        row = self.row()
        self.assertIsNone(row["taux_journalier_charge"])
        self.assertIsNone(row["taux_horaire_brut"])
        self.assertTrue(row["motif_indisponibilite"])

    def test_nonfinal_payrolls_are_excluded_and_empty_report_is_valid(self):
        for status in ("BROUILLON", "CALCULEE", "ANNULE"):
            self.payroll.statut = status
            self.payroll.save()
            self.assertEqual(self.report().data["employes"], [])
        self.payroll.statut = "PAYE"
        self.payroll.save()
        self.assertEqual(self.row()["paies_payees"], 1)

    def test_period_validation_and_access_control(self):
        for params in ({"periode_debut": "0000-01"}, {"periode_fin": "2026-13"}, {"periode_debut": "2026-11"}):
            self.assertEqual(self.report(**params).status_code, 400)
        self.employee.roles.clear()
        self.assertEqual(self.report().status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.report().status_code, 401)

    def test_project_costs_use_contract_hours_and_include_employee_breakdown(self):
        self.time_line()
        report = self.costs()
        self.assertEqual(report["totaux"]["cout_estime"], "4000.00")
        employee = report["projets"][0]["employes"][0]
        self.assertEqual(employee["employe_id"], self.employee.pk)
        self.assertEqual(employee["cout_estime"], "4000.00")

    def test_project_costs_missing_hours_or_foreign_currency_are_incomplete(self):
        self.time_line()
        self.contract.heures_journalieres = None
        self.contract.save()
        self.assertIsNone(self.costs()["totaux"]["cout_estime"])
        self.contract.heures_journalieres = Decimal("6")
        self.contract.save()
        self.payroll.devise = "EUR"
        self.payroll.save()
        report = self.costs()
        self.assertIsNone(report["totaux"]["cout_estime"])
        self.assertEqual(report["totaux"]["heures_sans_tgm"], "2.00")

    def test_project_costs_use_unrounded_rate_and_one_report_per_month(self):
        self.time_line(hours="3")
        self.payroll.cout_charge = Decimal("100")
        self.payroll.save()
        with patch.object(tgm_service, "calculate", wraps=tgm_service.calculate) as calculate:
            self.assertEqual(self.costs()["totaux"]["cout_estime"], "2.27")
            self.assertEqual(calculate.call_count, 1)

    def simulation(self, **changes):
        return self.client.get(reverse("rentabilite-projet"), {
            "date_debut": "2026-10-01", "date_fin": "2026-10-31",
            "projet": Projet.objects.get(code="TGM-PROJET").pk, "chiffre_affaires": "10000", **changes,
        })

    def test_simulation_calculates_margin_without_writing(self):
        self.time_line()
        with patch.object(Paie, "save", side_effect=AssertionError("Lecture seule")):
            response = self.simulation()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["marge_personnel"], "6000.00")
        self.assertEqual(response.data["taux_marge_personnel"], "60.00")
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_simulation_handles_loss_zero_revenue_and_incomplete_cost(self):
        self.time_line()
        self.assertEqual(self.simulation(chiffre_affaires="1000").data["marge_personnel"], "-3000.00")
        result = self.simulation(chiffre_affaires="0").data
        self.assertEqual(result["marge_personnel"], "-4000.00")
        self.assertIsNone(result["taux_marge_personnel"])
        self.contract.heures_journalieres = None
        self.contract.save()
        result = self.simulation().data
        self.assertIsNone(result["marge_personnel"])
        self.assertIsNone(result["taux_marge_personnel"])

    def test_simulation_validates_revenue_project_dates_and_permissions(self):
        self.time_line()
        for params in ({"chiffre_affaires": "-1"}, {"chiffre_affaires": "1.234"}, {"chiffre_affaires": "NaN"}, {"projet": 999999}, {"date_fin": "2026-09-30"}):
            self.assertEqual(self.simulation(**params).status_code, 400)
        self.employee.roles.clear()
        self.assertEqual(self.simulation().status_code, 403)

    def test_multi_month_rates_exclude_months_without_final_payroll(self):
        Paie.objects.create(employe=self.employee, periode="2026-09", statut="PAYE", salaire_brut="220000", cout_charge="264000")
        row = self.report(periode_debut="2026-08").data["employes"][0]
        self.assertEqual(row["periodes"], ["2026-09", "2026-10"])
        self.assertEqual(row["jours_ouvres_previsionnels"], 44)
        self.assertEqual(row["heures_previsionnelles"], "264.00")
        self.assertEqual(row["taux_horaire_charge"], "2000.00")

    def test_month_with_payroll_but_no_contract_does_not_inflate_average(self):
        Paie.objects.create(employe=self.employee, periode="2025-12", statut="PAYE", salaire_brut="220000", cout_charge="264000")
        row = self.report(periode_debut="2025-12").data["employes"][0]
        self.assertEqual(row["periodes_sans_jours"], ["2025-12"])
        self.assertIsNone(row["taux_journalier_charge"])
        self.assertIsNone(row["taux_horaire_charge"])

    def test_project_with_partly_missing_rates_keeps_subtotal_and_blocks_margin(self):
        line = self.time_line()
        other = Employe.objects.create_user(
            email="tgm-missing@example.com", password=None, nom="Autre", prenom="Test",
            matricule="TGM-002", num_secu_sociale="TGM-SSN-002", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )
        sheet = FeuilleTemps.objects.create(employe=other, semaine_debut=date(2026, 10, 19), statut="VALIDEE")
        LigneFeuilleTemps.objects.create(feuille=sheet, projet=line.projet, tache=line.tache, date_travail=date(2026, 10, 20), heures="1")
        report = self.simulation().data
        self.assertEqual(report["cout_calculable"], "4000.00")
        self.assertEqual(report["heures_sans_tgm"], "1.00")
        self.assertIsNone(report["marge_personnel"])
