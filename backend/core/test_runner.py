import os
from contextlib import ExitStack
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.storage import FileSystemStorage

from cryptography.fernet import Fernet
from django.test.runner import DiscoverRunner


class BankEncryptionTestRunner(DiscoverRunner):
    """Test databases use an ephemeral key, never the development key."""

    def setup_test_environment(self, **kwargs):
        self.previous_bank_key = os.environ.get("BANK_DATA_ENCRYPTION_KEY")
        os.environ["BANK_DATA_ENCRYPTION_KEY"] = Fernet.generate_key().decode("ascii")
        super().setup_test_environment(**kwargs)
        from core.models import Paie, OrdreVirement
        self.artifact_stack = ExitStack()
        directory = self.artifact_stack.enter_context(TemporaryDirectory(prefix="rh-test-artifacts-"))
        storage = FileSystemStorage(location=directory)
        for model, field in ((Paie, "bulletin_pdf"), (OrdreVirement, "document_pdf")):
            self.artifact_stack.enter_context(patch.object(model._meta.get_field(field), "storage", storage))

    def teardown_test_environment(self, **kwargs):
        try:
            super().teardown_test_environment(**kwargs)
        finally:
            self.artifact_stack.close()
            if self.previous_bank_key is None:
                os.environ.pop("BANK_DATA_ENCRYPTION_KEY", None)
            else:
                os.environ["BANK_DATA_ENCRYPTION_KEY"] = self.previous_bank_key
