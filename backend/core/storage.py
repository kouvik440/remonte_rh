from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivatePayrollStorage(FileSystemStorage):
    """Filesystem storage for payroll artifacts; it intentionally has no public URL."""

    def __init__(self, location=None, base_url=None):
        super().__init__(
            location=location or Path(settings.BASE_DIR) / "private_payroll_files",
            base_url=base_url,
        )
