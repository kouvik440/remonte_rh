from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import Employe, Paie, Role
from core.services.paie_service import paie_service


class PayrollAutomaticArchiveTests(APITestCase):
    def setUp(self):
        directory = TemporaryDirectory(prefix="rh-bulletin-test-")
        self.addCleanup(directory.cleanup)
        self.storage = FileSystemStorage(location=directory.name)
        storage_patch = patch.object(Paie._meta.get_field("bulletin_pdf"), "storage", self.storage)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        self.employee = Employe.objects.create_user(email="auto-archive@example.com", matricule="AUTO-ARCHIVE",
            nom="Test", prenom="Bulletin", num_secu_sociale="AUTO-SSN", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="000")
        self.manager = Employe.objects.create_user(email="archive-manager@example.com", matricule="AUTO-MANAGER",
            nom="Gestionnaire", prenom="Test", num_secu_sociale="AUTO-MANAGER-SSN", date_naissance="1990-01-01",
            date_entree="2020-01-01", adresse="Test", telephone="000")
        self.manager.roles.add(Role.objects.get(nom="FRONTEND_MODULE_4_PAIE_VIREMENTS"))
        self.client.force_authenticate(self.manager)
        self.payroll = Paie.objects.create(employe=self.employee, periode="2026-10", libelle="Salaire",
            statut="CALCULE", date_calcul=timezone.now(), salaire_base="300000", salaire_brut="300000",
            salaire_net="250000", cout_charge="330000", cotisations="80000",
            detail_calcul={"totaux": {"salaire_base": "300000", "salaire_brut": "300000",
                "salaire_net": "250000", "cout_charge": "330000"}, "cotisations": {}, "iuts": {}})

    def validate(self):
        return self.client.post(reverse("paie-valider", args=[self.payroll.pk]), {}, format="json")

    def test_validation_archives_pdf_and_owner_downloads_identical_bytes_without_generation(self):
        response = self.validate()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["bulletin_disponible"])
        self.payroll.refresh_from_db()
        name = self.payroll.bulletin_pdf.name
        with self.payroll.bulletin_pdf.open("rb") as stream:
            archived = stream.read()
        self.assertTrue(archived.startswith(b"%PDF"))
        self.assertEqual(self.payroll.valideur_id, self.manager.pk)
        self.assertIsNotNone(self.payroll.date_validation)
        # Retrying manual generation reuses the archived bytes even after identity changes.
        self.employee.nom = "Modifié après validation"
        self.employee.save()
        with patch.object(paie_service.bulletin_pdf_service, "render", side_effect=AssertionError("PDF régénéré")):
            again = self.client.post(reverse("paie-bulletin", args=[self.payroll.pk]), {}, format="json")
            self.assertEqual(again.status_code, 200)
            self.client.force_authenticate(self.employee)
            downloaded = self.client.get(reverse("paie-bulletin", args=[self.payroll.pk]))
            self.assertEqual(downloaded.status_code, 200)
            self.assertIn("private", downloaded["Cache-Control"])
            self.assertEqual(b"".join(downloaded.streaming_content), archived)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.bulletin_pdf.name, name)
        self.assertEqual(len(list(Path(self.storage.location).rglob("*.pdf"))), 1)
        with patch("django.core.signals.request_finished.send"):
            downloaded.close()

    def test_storage_failure_rolls_back_validation_and_allows_retry(self):
        with patch.object(self.storage, "save", side_effect=OSError("Storage unavailable")):
            response = self.validate()
        self.assertEqual(response.status_code, 400, response.data)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.statut, "CALCULE")
        self.assertIsNone(self.payroll.date_validation)
        self.assertIsNone(self.payroll.valideur_id)
        self.assertFalse(self.payroll.bulletin_pdf)
        self.assertEqual(self.validate().status_code, 200)

    def test_missing_calculation_snapshot_cannot_validate_without_pdf(self):
        self.payroll.detail_calcul = {}
        self.payroll.save()
        response = self.validate()
        self.assertEqual(response.status_code, 400, response.data)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.statut, "CALCULE")
        self.assertFalse(self.payroll.bulletin_pdf)

    def test_second_validation_is_rejected_without_creating_another_pdf(self):
        self.assertEqual(self.validate().status_code, 200)
        self.assertEqual(self.validate().status_code, 400)
        self.assertEqual(len(list(Path(self.storage.location).rglob("*.pdf"))), 1)

    def test_database_failure_after_file_write_cleans_up_file_and_rolls_back_validation(self):
        original_save = Paie.save

        def fail_archive_save(instance, *args, **kwargs):
            if instance.bulletin_pdf:
                raise RuntimeError("Database save failed")
            return original_save(instance, *args, **kwargs)

        with patch.object(Paie, "save", fail_archive_save), self.assertRaises(RuntimeError):
            paie_service.valider(self.payroll.pk, self.manager.pk)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.statut, "CALCULE")
        self.assertIsNone(self.payroll.date_validation)
        self.assertEqual(list(Path(self.storage.location).rglob("*.pdf")), [])
