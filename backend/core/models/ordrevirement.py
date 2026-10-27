from django.db import models
from core.fields import EncryptedBankTextField
from core.storage import PrivatePayrollStorage
from .enums import StatutVirement

class OrdreVirement(models.Model):
    periode = models.CharField(max_length=100)
    statut = models.CharField(
        max_length=20,
        choices=StatutVirement.choices,
        default=StatutVirement.GENERE,
    )
    date_generation = models.DateTimeField()
    date_traitement = models.DateTimeField(null=True, blank=True)
    date_decision = models.DateTimeField(null=True, blank=True)
    motif_decision = models.CharField(max_length=500, blank=True)
    document_donnees = EncryptedBankTextField(blank=True, default="")
    document_pdf = models.FileField(upload_to="ordres_virement/", storage=PrivatePayrollStorage(), null=True, blank=True)
    document_genere_le = models.DateTimeField(null=True, blank=True)
    document_genere_par = models.ForeignKey(
        "core.Employe", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="documents_virement_generes",
    )
    decideur = models.ForeignKey(
        "core.Employe", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="decisions_ordres_virement",
    )
    employe = models.ForeignKey(
        "core.Employe",
        on_delete=models.CASCADE,
        related_name="ordres_virement",
    )

    class Meta:
        ordering = ["date_generation", "periode"]

    def __str__(self):
        return f"{self.periode} - {self.employe}"
