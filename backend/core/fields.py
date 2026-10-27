from django.db import models
from django.db.utils import NotSupportedError

from core.security import decrypt_bank_value, encrypt_bank_value, iban_fingerprint


class EncryptedBankTextField(models.TextField):
    """Convert at the storage boundary, including ORM inserts and updates."""

    def from_db_value(self, value, expression, connection):
        return decrypt_bank_value(value) if value is not None else None

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_bank_value(value) if value is not None else None

    def get_lookup(self, lookup_name):
        if lookup_name != "isnull":
            raise NotSupportedError("Encrypted bank fields cannot be searched; use the IBAN fingerprint.")
        return super().get_lookup(lookup_name)


class IbanFingerprintField(models.CharField):
    def pre_save(self, model_instance, add):
        fingerprint = iban_fingerprint(model_instance.iban)
        setattr(model_instance, self.attname, fingerprint)
        return fingerprint
