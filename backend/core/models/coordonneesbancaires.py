from django.db import models
from core.fields import EncryptedBankTextField, IbanFingerprintField
from core.security import iban_fingerprint


class BankDetailsQuerySet(models.QuerySet):
    def update(self, **kwargs):
        for name in ("iban", "bic", "swift"):
            if name in kwargs and not isinstance(kwargs[name], str):
                raise ValueError("Encrypted bank updates require literal text values.")
        if "iban" in kwargs:
            kwargs["iban_fingerprint"] = iban_fingerprint(kwargs["iban"])
        return super().update(**kwargs)

class CoordonneesBancaires(models.Model):
    iban = EncryptedBankTextField(max_length=34)
    bic = EncryptedBankTextField(max_length=11, blank=True)
    swift = EncryptedBankTextField(max_length=11, blank=True)
    iban_fingerprint = IbanFingerprintField(max_length=64, unique=True, editable=False)
    banque = models.CharField(max_length=100)
    date_modification = models.DateTimeField(auto_now=True)
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="coordonnees_bancaires",
    )

    class Meta:
        ordering = ["banque"]

    objects = BankDetailsQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if kwargs.get("update_fields") and "iban" in kwargs["update_fields"]:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"iban_fingerprint"}
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.banque
