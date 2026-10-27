from django.db import migrations, models

import core.fields
from core.security import encrypt_bank_value, iban_fingerprint, validate_bank_encryption_key


def encrypt_existing_details(apps, schema_editor):
    validate_bank_encryption_key()
    model = apps.get_model("core", "CoordonneesBancaires")
    records = model.objects.using(schema_editor.connection.alias).all()
    fingerprints = set()
    for record in records.iterator():
        fingerprint = iban_fingerprint(record.iban)
        if fingerprint in fingerprints:
            raise ValueError("Duplicate normalized IBANs: migration cancelled without exposing account values.")
        fingerprints.add(fingerprint)
    for record in records.iterator():
        record.iban_fingerprint = iban_fingerprint(record.iban)
        for name in ("iban", "bic", "swift"):
            setattr(record, name, encrypt_bank_value(getattr(record, name)))
        record.save(using=schema_editor.connection.alias, update_fields=["iban", "bic", "swift", "iban_fingerprint"])


class Migration(migrations.Migration):
    atomic = True
    dependencies = [("core", "0032_document_manage_permission")]
    operations = [
        migrations.AlterField(model_name="coordonneesbancaires", name="iban", field=models.TextField(max_length=34)),
        migrations.AlterField(model_name="coordonneesbancaires", name="bic", field=models.TextField(blank=True, max_length=11)),
        migrations.AlterField(model_name="coordonneesbancaires", name="swift", field=models.TextField(blank=True, max_length=11)),
        migrations.AddField(model_name="coordonneesbancaires", name="iban_fingerprint", field=models.CharField(max_length=64, unique=True, null=True, editable=False)),
        migrations.RunPython(encrypt_existing_details),
        migrations.AlterField(model_name="coordonneesbancaires", name="iban", field=core.fields.EncryptedBankTextField(max_length=34)),
        migrations.AlterField(model_name="coordonneesbancaires", name="bic", field=core.fields.EncryptedBankTextField(blank=True, max_length=11)),
        migrations.AlterField(model_name="coordonneesbancaires", name="swift", field=core.fields.EncryptedBankTextField(blank=True, max_length=11)),
        migrations.AlterField(model_name="coordonneesbancaires", name="iban_fingerprint", field=core.fields.IbanFingerprintField(max_length=64, unique=True, editable=False)),
    ]
