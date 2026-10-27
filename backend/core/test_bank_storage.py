import os
from datetime import date
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.db.utils import NotSupportedError
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import CoordonneesBancaires, Employe, Role
from core.permission_codes import get_permission_by_code
from core.security import iban_fingerprint


class BankStorageEncryptionTests(APITestCase):
    def setUp(self):
        self.employee = Employe.objects.create_user(
            email="encrypted-bank@example.com", password="TestPassword123!", matricule="ENCRYPTED-001",
            nom="Test", prenom="Encryption", date_naissance=date(1990, 1, 1),
            date_entree=date(2020, 1, 1), adresse="Test", telephone="0000", num_secu_sociale="ENCRYPTED-SSN",
        )
        role = Role.objects.create(nom="BANK_ENCRYPTION_TEST")
        role.permissions.add(*[get_permission_by_code(f"coordonnees_bancaires.{action}") for action in ("read", "create", "update")])
        self.employee.roles.add(role)
        self.client.force_authenticate(user=self.employee)
        self.payload = {"iban": "FR761234567890", "bic": "BANKFRPP", "swift": "BANKFRPPXXX", "banque": "Test"}

    def raw_values(self, record_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT iban, bic, swift, iban_fingerprint FROM core_coordonneesbancaires WHERE id = %s", [record_id])
            return cursor.fetchone()

    def create_details(self, **overrides):
        return CoordonneesBancaires.objects.create(employe=self.employee, **{**self.payload, **overrides})

    def test_api_encrypts_storage_and_keeps_authorized_response_readable(self):
        response = self.client.post(reverse("coordonnees-bancaires-list"), self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        raw = self.raw_values(response.data["id"])
        for index, name in enumerate(("iban", "bic", "swift")):
            self.assertNotEqual(raw[index], self.payload[name])
            self.assertTrue(raw[index].startswith("gAAAA"))
            self.assertEqual(response.data[name], self.payload[name])
        self.assertEqual(raw[3], iban_fingerprint(self.payload["iban"]))
        self.assertNotIn("iban_fingerprint", response.data)
        detail = self.client.get(reverse("coordonnees-bancaires-detail", args=[response.data["id"]]))
        self.assertEqual(detail.data["iban"], self.payload["iban"])

    def test_normalized_duplicate_returns_validation_error(self):
        self.create_details()
        response = self.client.post(reverse("coordonnees-bancaires-list"), {
            **self.payload, "iban": "fr76 1234 5678 90",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("iban", response.data)
        self.assertEqual(CoordonneesBancaires.objects.count(), 1)

    def test_duplicate_update_does_not_change_stored_account(self):
        first = self.create_details()
        second = self.create_details(iban="FR760000000000")
        response = self.client.put(reverse("coordonnees-bancaires-detail", args=[second.pk]), self.payload, format="json")
        self.assertEqual(response.status_code, 400)
        second.refresh_from_db()
        self.assertEqual(second.iban, "FR760000000000")
        self.assertNotEqual(self.raw_values(first.pk)[3], self.raw_values(second.pk)[3])

    def test_queryset_update_encrypts_and_updates_fingerprint(self):
        record = self.create_details()
        CoordonneesBancaires.objects.filter(pk=record.pk).update(iban="FR760000000000", bic="NEWBIC")
        record.refresh_from_db()
        raw = self.raw_values(record.pk)
        self.assertEqual(record.bic, "NEWBIC")
        self.assertNotEqual(raw[1], "NEWBIC")
        self.assertEqual(raw[3], iban_fingerprint("FR760000000000"))

    def test_partial_save_refreshes_fingerprint_and_bulk_create_is_encrypted(self):
        record = self.create_details()
        record.iban = "FR760000000000"
        record.save(update_fields=["iban"])
        self.assertEqual(self.raw_values(record.pk)[3], iban_fingerprint(record.iban))
        bulk = CoordonneesBancaires(employe=self.employee, **self.payload)
        CoordonneesBancaires.objects.bulk_create([bulk])
        self.assertNotEqual(self.raw_values(bulk.pk)[0], self.payload["iban"])
        self.assertEqual(self.raw_values(bulk.pk)[3], iban_fingerprint(self.payload["iban"]))

    @override_settings(BANK_DATA_ENCRYPTION_KEY_FILE="")
    def test_missing_key_fails_without_writing_plaintext(self):
        with patch.dict(os.environ, {"BANK_DATA_ENCRYPTION_KEY": "", "BANK_DATA_ENCRYPTION_KEY_FILE": ""}):
            with self.assertRaises(ImproperlyConfigured):
                with transaction.atomic():
                    self.create_details()
        self.assertFalse(CoordonneesBancaires.objects.exists())

    def test_wrong_key_cannot_read_encrypted_data(self):
        record = self.create_details()
        with patch.dict(os.environ, {"BANK_DATA_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii")}):
            with self.assertRaises(ImproperlyConfigured):
                CoordonneesBancaires.objects.get(pk=record.pk)

    def test_searching_randomized_ciphertext_is_explicitly_rejected(self):
        with self.assertRaises(NotSupportedError):
            CoordonneesBancaires.objects.filter(iban=self.payload["iban"]).exists()
