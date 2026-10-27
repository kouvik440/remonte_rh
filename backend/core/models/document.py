from django.db import models
from .enums import StatutEmploye, StatutContrat

class Document(models.Model):
    type_document = models.ForeignKey(
        "core.TypeDocument",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    fichier = models.CharField(max_length=255)
    date_depot = models.DateField()
    date_expiration = models.DateField(null=True, blank=True)
    employes = models.ManyToManyField(
        "core.Employe",
        through="DocumentEmploye",
        related_name="documents",
    )

    class Meta:
        ordering = ["date_depot", "type_document"]

    def __str__(self):
        return f"{self.type_document.libelle} - {self.fichier}"