import csv
from io import BytesIO, StringIO
from xml.etree import ElementTree
from zipfile import ZipFile

from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Departement, Employe, Paie, Role


class MassEvolutionExportTests(APITestCase):
    def setUp(self):
        self.first = self.employee("A")
        self.second = self.employee("B")
        self.department = Departement.objects.create(nom="Analyse A", code="AN-A")
        self.other_department = Departement.objects.create(nom="Analyse B", code="AN-B")
        self.first.roles.add(Role.objects.get(nom="FRONTEND_MODULE_5_MASSE_SALARIALE"))
        self.client.force_authenticate(self.first)
        for period, employee, department, status, amount in (
            ("2025-12", self.first, self.department, "VALIDEE", 1000),
            ("2026-01", self.first, self.department, "VALIDEE", 2000),
            ("2026-02", self.first, self.department, "PAYE", 3000),
            ("2026-03", self.second, self.other_department, "PAYE", 4000),
            ("2026-04", self.second, self.other_department, "BROUILLON", 5000),
            ("2026-05", self.second, self.other_department, "ANNULE", 6000),
        ):
            Paie.objects.create(
                employe=employee, periode=period, statut=status,
                salaire_brut=amount, salaire_net=amount * 8 // 10,
                cotisations=amount // 10, cout_charge=amount * 11 // 10,
                detail_calcul={"classification": {
                    "departement": {"id": department.pk, "nom": department.nom},
                    "types_contrat": [],
                }},
            )
        self.query = {"periode_debut": "2025-12", "periode_fin": "2026-12"}

    def employee(self, suffix):
        return Employe.objects.create_user(
            email=f"mass-export-{suffix}@example.com", password=None,
            matricule=f"MEX-{suffix}", num_secu_sociale=f"MEX-SSN-{suffix}",
            nom="Analyse", prenom=suffix, date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="0000",
        )

    def export(self, format_name, **params):
        return self.client.get(reverse("masse-salariale-export"), {
            **self.query, "format_fichier": format_name, **params,
        })

    def test_annual_evolution_preserves_distinct_employees_costs_and_contributions(self):
        response = self.client.get(reverse("masse-salariale-evolution"), {**self.query, "granularite": "annuelle"})
        self.assertEqual(response.status_code, 200)
        old_year, year = response.data["evolution"]
        self.assertEqual(old_year["annee"], "2025")
        self.assertEqual(year["annee"], "2026")
        self.assertEqual(year["employes"], 2)
        for key, value in {"brut_valide": "2000.00", "brut_paye": "7000.00",
                           "cotisations_validees": "200.00", "cotisations_payees": "700.00",
                           "cout_employeur_valide": "2200.00", "cout_employeur_paye": "7700.00"}.items():
            self.assertEqual(year[key], value)

    def test_annual_csv_matches_filtered_evolution_and_deduplicates_employees(self):
        params = {"granularite": "annuelle", "departement": self.department.pk}
        response = self.export("csv", **params)
        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
        index = rows.index(["Evolution annuelle"])
        headers, first_year, last_year = rows[index + 1:index + 4]
        self.assertEqual(headers[:2], ["Annee", "Employes"])
        self.assertEqual(first_year[:2], ["2025", "1"])
        self.assertEqual(last_year[:2], ["2026", "1"])
        exported = dict(zip(headers, last_year))
        self.assertEqual(exported["Cout employeur paye (XOF)"], "3300.00")
        self.assertEqual(exported["Cotisations payees (XOF)"], "300.00")
        self.assertEqual(exported["Net paye (XOF)"], "2400.00")
        self.assertIn("annuelle.csv", response["Content-Disposition"])

    def test_monthly_export_remains_default_and_preserves_months(self):
        response = self.export("csv")
        rows = list(csv.reader(StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
        index = rows.index(["Evolution mensuelle"])
        self.assertEqual([row[0] for row in rows[index + 2:index + 6]], ["2025-12", "2026-01", "2026-02", "2026-03"])

    def test_annual_excel_contains_annual_rows_and_numeric_costs(self):
        response = self.export("xlsx", granularite="annuelle")
        self.assertEqual(response.status_code, 200)
        with ZipFile(BytesIO(response.content)) as archive:
            workbook = archive.read("xl/workbook.xml").decode()
            self.assertIn('name="Evolution annuelle"', workbook)
            sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet2.xml"))
        namespace = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        rows = sheet.findall("s:sheetData/s:row", namespace)
        self.assertEqual(len(rows), 3)
        values = {cell.attrib["r"]: cell.findtext("s:v", namespaces=namespace) for cell in rows[2]}
        self.assertEqual(values["A3"], "2026")
        self.assertEqual(values["B3"], "2")
        self.assertEqual(values["K3"], "700.00")
        self.assertEqual(values["L3"], "7700.00")

    def test_annual_pdf_is_generated_with_matching_granularity(self):
        response = self.export("pdf", granularite="annuelle")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertTrue(response.content.rstrip().endswith(b"%%EOF"))
        self.assertIn("annuelle.pdf", response["Content-Disposition"])

    def test_export_rejects_unknown_granularity(self):
        response = self.export("csv", granularite="hebdomadaire")
        self.assertEqual(response.status_code, 400)
        self.assertIn("granularite", response.data)
