import base64
import hashlib
import hmac
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings


_KEY_ENVIRONMENT_VARIABLE = "BANK_DATA_ENCRYPTION_KEY"
_FINGERPRINT_CONTEXT = b"remonte-rh:iban-fingerprint:v1"


def _get_fernet_and_fingerprint_key() -> tuple[Fernet, bytes]:
    encoded_key = os.environ.get(_KEY_ENVIRONMENT_VARIABLE)
    if not encoded_key:
        key_file = os.environ.get("BANK_DATA_ENCRYPTION_KEY_FILE", settings.BANK_DATA_ENCRYPTION_KEY_FILE)
        if key_file:
            try:
                encoded_key = Path(key_file).read_text(encoding="ascii").strip()
            except (OSError, UnicodeError) as error:
                raise ImproperlyConfigured("Bank encryption key file is missing or unreadable.") from error
    if not encoded_key:
        raise ImproperlyConfigured(
            f"Set {_KEY_ENVIRONMENT_VARIABLE} before using bank data."
        )

    try:
        key = encoded_key.encode("ascii")
        fernet = Fernet(key)
        raw_key = base64.urlsafe_b64decode(key)
    except (UnicodeEncodeError, ValueError) as error:
        raise ImproperlyConfigured(
            f"{_KEY_ENVIRONMENT_VARIABLE} must be a valid Fernet key."
        ) from error

    fingerprint_key = hmac.new(
        raw_key,
        _FINGERPRINT_CONTEXT,
        hashlib.sha256,
    ).digest()
    return fernet, fingerprint_key


def validate_bank_encryption_key() -> None:
    _get_fernet_and_fingerprint_key()


def encrypt_bank_value(value: str) -> str:
    if value == "":
        return value
    fernet, _ = _get_fernet_and_fingerprint_key()
    return fernet.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_bank_value(value: str) -> str:
    if value == "":
        return value
    fernet, _ = _get_fernet_and_fingerprint_key()
    try:
        return fernet.decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError) as error:
        raise ImproperlyConfigured(
            "Bank data could not be decrypted with the configured key."
        ) from error


def iban_fingerprint(iban: str) -> str:
    _, fingerprint_key = _get_fernet_and_fingerprint_key()
    normalized_iban = "".join(iban.split()).upper().encode("utf-8")
    return hmac.new(fingerprint_key, normalized_iban, hashlib.sha256).hexdigest()
