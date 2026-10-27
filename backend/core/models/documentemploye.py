from django.db import models
from .document import Document
from .enums import StatutEmploye
from .employe import Employe

class DocumentEmploye(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="document_employe",
    )
    date_depot = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ("document", "employe")

    def __str__(self):
        return f"{self.document} - {self.employe}"
